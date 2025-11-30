"""
Orquestador Principal del Sistema Agentic AI.
Coordina el flujo entre todos los agentes especializados usando LLM para decisiones.
"""
import logging
from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.agents.classifier_agent import ClassifierAgent
from src.agents.retriever_agent import RetrieverAgent
from src.agents.rag_agent import RAGAgent
from src.agents.critic_agent import CriticAgent
from src.config.llm_config import llm_config
from src.utils.tracing import trace_manager, ExecutionTrace
from src.utils.formatting import format_response_with_citations, format_trace_summary

logger = logging.getLogger(__name__)


class OrchestrationDecision(BaseModel):
    """Decisión del orquestador sobre cómo procesar la consulta."""
    strategy: str = Field(description="Estrategia a seguir: direct_response, simple_rag, comparison_rag, summary_rag, multi_hop")
    num_documents: int = Field(description="Número de documentos a recuperar (0 si no aplica)")
    retrieval_mode: str = Field(description="Modo de recuperación: standard, comparison, summary, none")
    needs_validation: bool = Field(description="Si requiere validación crítica")
    reasoning: str = Field(description="Justificación de la decisión")


class Orchestrator:
    """
    Orquestador Principal del Sistema Agentic AI.
    
    Usa LLM (Groq) para tomar decisiones inteligentes sobre:
    - Estrategia de procesamiento óptima
    - Número de documentos a recuperar
    - Modo de recuperación según contexto
    - Necesidad de validación crítica
    """
    
    def __init__(self):
        """Inicializa el orquestador y todos los agentes."""
        logger.info("Inicializando Orchestrator con LLM...")
        
        # Inicializar agentes
        self.classifier = ClassifierAgent()
        self.retriever = RetrieverAgent()
        self.rag_agent = RAGAgent()
        self.critic = CriticAgent()
        
        # LLM para decisiones de orquestación
        self.llm = llm_config.get_orchestrator_llm()
        self.structured_llm = self.llm.with_structured_output(OrchestrationDecision)
        
        # Prompt para decisiones
        self.decision_prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_decision_prompt()),
            ("user", "Consulta: {query}\nIntención: {intent}\nConfianza: {confidence}\nRequiere RAG: {requires_rag}")
        ])
        
        logger.info("Orchestrator inicializado con todos los agentes + LLM de decisión")
    
    def _get_decision_prompt(self) -> str:
        """Genera el prompt para decisiones de orquestación."""
        return """Eres un orquestador experto de sistemas RAG. Tu tarea es decidir la mejor estrategia para procesar consultas.

ESTRATEGIAS DISPONIBLES:

1. **direct_response**: Respuesta directa sin RAG (conversación, saludos, preguntas generales)
   - num_documents: 0
   - retrieval_mode: none
   - needs_validation: false

2. **simple_rag**: Búsqueda simple de información específica
   - num_documents: 3-5
   - retrieval_mode: standard
   - needs_validation: true

3. **comparison_rag**: Comparación entre 2+ conceptos/documentos
   - num_documents: 4-6
   - retrieval_mode: comparison
   - needs_validation: true

4. **summary_rag**: Resumen de documentos
   - num_documents: 8-10
   - retrieval_mode: summary
   - needs_validation: true

5. **multi_hop**: Preguntas complejas que requieren múltiples consultas
   - num_documents: 5-8
   - retrieval_mode: standard
   - needs_validation: true

CRITERIOS DE DECISIÓN:
- Analiza la complejidad y contexto de la consulta
- Optimiza el número de documentos (más no siempre es mejor)
- Valida respuestas técnicas/médicas, no conversaciones simples
- Considera la intención clasificada pero usa tu criterio

Responde SOLO con los campos del modelo OrchestrationDecision.
"""
    
    def _decide_strategy(self, query: str, classification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Usa LLM para decidir la estrategia óptima de procesamiento.
        
        Args:
            query: Consulta del usuario
            classification: Clasificación de intención
            
        Returns:
            Decisión de orquestación
        """
        try:
            logger.info("Usando LLM para decidir estrategia de orquestación...")
            
            messages = self.decision_prompt.format_messages(
                query=query,
                intent=classification["intent"],
                confidence=classification["confidence"],
                requires_rag=classification["requires_rag"]
            )
            
            decision = self.structured_llm.invoke(messages)
            
            result = {
                "strategy": decision.strategy,
                "num_documents": decision.num_documents,
                "retrieval_mode": decision.retrieval_mode,
                "needs_validation": decision.needs_validation,
                "reasoning": decision.reasoning
            }
            
            logger.info(f"Estrategia decidida: {decision.strategy} ({decision.reasoning[:100]}...)")
            return result
            
        except Exception as e:
            logger.error(f"Error en decisión LLM, usando fallback: {str(e)}")
            # Fallback basado en clasificación
            intent = classification["intent"]
            return {
                "strategy": "direct_response" if not classification["requires_rag"] else "simple_rag",
                "num_documents": 0 if not classification["requires_rag"] else 5,
                "retrieval_mode": "none" if not classification["requires_rag"] else "standard",
                "needs_validation": classification["requires_rag"],
                "reasoning": f"Fallback basado en clasificación: {intent}"
            }
    
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
            
            logger.info(f"Intención detectada: {classification['intent']} (confianza: {classification['confidence']:.2f})")
            
            # PASO 2: Decisión de Estrategia con LLM
            logger.info("PASO 2: Decidiendo estrategia con LLM...")
            decision = self._decide_strategy(query, classification)
            
            trace.add_step(
                agent="orchestrator_llm",
                action="strategy_decision",
                details={
                    "strategy": decision["strategy"],
                    "num_documents": decision["num_documents"],
                    "reasoning": decision["reasoning"],
                    "llm_call": True
                }
            )
            
            logger.info(f"Estrategia: {decision['strategy']} | Docs: {decision['num_documents']}")
            
            # PASO 3: Ejecutar según estrategia decidida
            if decision["strategy"] == "direct_response":
                # Respuesta directa sin RAG usando el LLM del clasificador (Gemini)
                logger.info("PASO 3: Generando respuesta directa con Clasificador LLM (Gemini)...")
                
                # Usar el LLM del clasificador para respuestas generales
                from langchain_core.prompts import ChatPromptTemplate
                
                general_prompt = ChatPromptTemplate.from_messages([
                    ("system", "Eres un asistente amigable y útil. Responde de manera conversacional y natural."),
                    ("user", "{query}")
                ])
                
                messages = general_prompt.format_messages(query=query)
                response = self.classifier.llm.invoke(messages)
                response_text = response.content
                
                trace.add_general_response(response_text)
                trace.finalize(response_text)
                
                return {
                    "response": response_text,
                    "intent": classification["intent"],
                    "strategy": decision["strategy"],
                    "requires_rag": False,
                    "llm_used": "classifier_gemini",
                    "trace": trace.to_dict() if include_trace else None,
                    "session_id": trace.session_id
                }
            
            # PASO 3: Recuperación de Documentos según modo
            logger.info(f"PASO 3: Recuperando documentos (modo: {decision['retrieval_mode']})...")
            
            if decision["retrieval_mode"] == "comparison":
                documents = self.retriever.retrieve_for_comparison(query, num_docs=decision["num_documents"])
            elif decision["retrieval_mode"] == "summary":
                documents = self.retriever.retrieve_for_summary(query, max_docs=decision["num_documents"])
            else:  # standard
                documents = self.retriever.retrieve(query, k=decision["num_documents"], optimize=True, intent=classification["intent"])
            
            if not documents:
                logger.warning("No se encontraron documentos relevantes")
                error_response = "No encontré documentos relevantes para responder tu consulta. Intenta reformular la pregunta."
                trace.finalize(error_response)
                
                return {
                    "response": error_response,
                    "intent": classification["intent"],
                    "strategy": decision["strategy"],
                    "requires_rag": True,
                    "documents_found": 0,
                    "trace": trace.to_dict() if include_trace else None,
                    "session_id": trace.session_id
                }
            
            trace.add_retrieval(documents)
            
            # PASO 4: Generación de Respuesta RAG
            logger.info("PASO 4: Generando respuesta con RAG...")
            response_data = self.rag_agent.generate_response(
                query=query,
                documents=documents,
                intent=classification["intent"]
            )
            
            response_text = response_data["response"]
            sources = response_data["sources"]
            
            trace.add_generation(
                response=response_text,
                context_used=[doc.get('content', '')[:200] for doc in documents],
                citations=[s.get('file_name', '') for s in sources]
            )
            
            # PASO 5: Validación Crítica (si es necesario)
            if decision["needs_validation"]:
                logger.info("PASO 5: Validando respuesta con crítico...")
                
                def regenerate_callback(query, documents, previous_issues):
                    """Callback para regeneración de respuesta."""
                    logger.info(f"Regenerando respuesta (issues previos: {len(previous_issues)})")
                    return self.rag_agent.generate_response(query, documents, classification["intent"])
                
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
            else:
                logger.info("PASO 5: Validación omitida (no requerida por estrategia)")
                final_response = response_text
                validation = {"is_valid": True, "skipped": True}
                validation_result = {"attempts": 1}
            
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
                "intent": classification["intent"],
                "strategy": decision["strategy"],
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