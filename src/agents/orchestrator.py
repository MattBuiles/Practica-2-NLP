"""
Orquestador Principal del Sistema Agentic AI.
Coordina el flujo entre todos los agentes especializados.
"""
import logging
from typing import Dict, Any, Optional

from src.agents.classifier_agent import ClassifierAgent
from src.agents.retriever_agent import RetrieverAgent
from src.agents.rag_agent import RAGAgent
from src.agents.critic_agent import CriticAgent
from src.utils.tracing import trace_manager, ExecutionTrace
from src.utils.formatting import format_response_with_citations, format_trace_summary

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Orquestador Principal del Sistema Agentic AI.
    
    Responsable de:
    - Coordinar el flujo entre agentes
    - Gestionar trazabilidad
    - Manejar errores y fallbacks
    - Decidir el routing según intención
    """
    
    def __init__(self):
        """Inicializa el orquestador y todos los agentes."""
        logger.info("Inicializando Orchestrator...")
        
        # Inicializar agentes
        self.classifier = ClassifierAgent()
        self.retriever = RetrieverAgent()
        self.rag_agent = RAGAgent()
        self.critic = CriticAgent()
        
        logger.info("Orchestrator inicializado con todos los agentes")
    
    def process_query(self, query: str, session_id: Optional[str] = None,
                     include_trace: bool = True) -> Dict[str, Any]:
        """
        Procesa una consulta completa a través del sistema.
        
        Args:
            query: Consulta del usuario
            session_id: ID de sesión (opcional)
            include_trace: Si incluir información de trazabilidad
            
        Returns:
            Diccionario con respuesta y metadata
        """
        logger.info(f"=== Procesando consulta: {query[:100]}... ===")
        
        # Iniciar traza
        trace = trace_manager.start_trace(query, session_id)
        
        try:
            # PASO 1: Clasificación de Intención
            logger.info("PASO 1: Clasificando intención...")
            classification = self.classifier.classify(query)
            
            trace.add_classification(
                intent=classification["intent"],
                confidence=classification["confidence"],
                reasoning=classification["reasoning"]
            )
            
            intent = classification["intent"]
            requires_rag = classification["requires_rag"]
            
            logger.info(f"Intención detectada: {intent} (RAG: {requires_rag})")
            
            # PASO 2: Routing según intención
            if not requires_rag:
                # Consulta general - respuesta directa sin RAG
                logger.info("PASO 2: Generando respuesta general (sin RAG)...")
                response_text = self.rag_agent.generate_general_response(query)
                
                trace.add_general_response(response_text)
                trace.finalize(response_text)
                
                return {
                    "response": response_text,
                    "intent": intent,
                    "requires_rag": False,
                    "trace": trace.to_dict() if include_trace else None,
                    "session_id": trace.session_id
                }
            
            # PASO 2: Recuperación de Documentos
            logger.info("PASO 2: Recuperando documentos relevantes...")
            
            if intent == "comparacion":
                documents = self.retriever.retrieve_for_comparison(query, num_docs=4)
            elif intent == "resumen":
                documents = self.retriever.retrieve_for_summary(query, max_docs=10)
            else:  # busqueda
                documents = self.retriever.retrieve(query, k=5, optimize=True, intent=intent)
            
            if not documents:
                logger.warning("No se encontraron documentos relevantes")
                error_response = "No encontré documentos relevantes para responder tu consulta. Intenta reformular la pregunta."
                trace.finalize(error_response)
                
                return {
                    "response": error_response,
                    "intent": intent,
                    "requires_rag": True,
                    "documents_found": 0,
                    "trace": trace.to_dict() if include_trace else None,
                    "session_id": trace.session_id
                }
            
            trace.add_retrieval(documents)
            
            # PASO 3: Generación de Respuesta RAG
            logger.info("PASO 3: Generando respuesta con RAG...")
            response_data = self.rag_agent.generate_response(
                query=query,
                documents=documents,
                intent=intent
            )
            
            response_text = response_data["response"]
            sources = response_data["sources"]
            
            trace.add_generation(
                response=response_text,
                context_used=[doc.get('content', '')[:200] for doc in documents],
                citations=[s.get('file_name', '') for s in sources]
            )
            
            # PASO 4: Validación Crítica
            logger.info("PASO 4: Validando respuesta...")
            
            def regenerate_callback(query, documents, previous_issues):
                """Callback para regeneración de respuesta."""
                logger.info(f"Regenerando respuesta (issues previos: {len(previous_issues)})")
                return self.rag_agent.generate_response(query, documents, intent)
            
            validation_result = self.critic.validate_with_regeneration(
                query=query,
                response=response_text,
                context_docs=documents,
                regenerate_callback=regenerate_callback,
                max_attempts=2
            )
            
            final_response = validation_result["final_response"]
            validation = validation_result["validation"]
            
            trace.add_validation(
                is_valid=validation.get("is_valid", True),
                validation_results=validation,
                needs_regeneration=validation.get("needs_regeneration", False)
            )
            
            # Finalizar traza
            trace.finalize(final_response)
            
            # Formatear respuesta con fuentes
            formatted_response = self.rag_agent.format_response_with_sources(
                {"response": final_response, "sources": sources}
            )
            
            logger.info("=== Consulta procesada exitosamente ===")
            
            return {
                "response": formatted_response,
                "raw_response": final_response,
                "intent": intent,
                "requires_rag": True,
                "documents_found": len(documents),
                "sources": sources,
                "validation": validation,
                "regeneration_attempts": validation_result.get("attempts", 1) - 1,
                "trace": trace.to_dict() if include_trace else None,
                "trace_summary": trace.get_summary() if include_trace else None,
                "session_id": trace.session_id
            }
            
        except Exception as e:
            logger.error(f"Error en procesamiento: {str(e)}", exc_info=True)
            
            error_response = f"Ocurrió un error al procesar tu consulta: {str(e)}"
            trace.finalize(error_response)
            
            return {
                "response": error_response,
                "error": str(e),
                "trace": trace.to_dict() if include_trace else None,
                "session_id": trace.session_id
            }
    
    def process_batch(self, queries: list[str]) -> list[Dict[str, Any]]:
        """
        Procesa múltiples consultas en lote.
        
        Args:
            queries: Lista de consultas
            
        Returns:
            Lista de resultados
        """
        logger.info(f"Procesando lote de {len(queries)} consultas...")
        
        results = []
        for i, query in enumerate(queries, 1):
            logger.info(f"--- Consulta {i}/{len(queries)} ---")
            result = self.process_query(query, include_trace=True)
            results.append(result)
        
        logger.info(f"Lote procesado: {len(results)} resultados")
        return results
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del sistema.
        
        Returns:
            Diccionario con estadísticas
        """
        from src.rag_pipeline.vectorstore import vectorstore_manager
        
        stats = {
            "agents": {
                "classifier": "ClassifierAgent (Gemini)",
                "retriever": "RetrieverAgent (Groq)",
                "rag": "RAGAgent (Groq)",
                "critic": "CriticAgent (Gemini)"
            },
            "vectorstore": vectorstore_manager.get_index_stats(),
            "traces_collected": len(trace_manager.get_all_traces())
        }
        
        return stats