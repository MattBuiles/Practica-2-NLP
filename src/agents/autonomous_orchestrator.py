"""
Orquestador Autónomo con Agentes y Tools.
Coordina el flujo completo del sistema usando agentes autónomos.
"""
import logging
from typing import Dict, Any
from datetime import datetime

from src.agents.autonomous_classifier_agent import AutonomousClassifierAgent
from src.agents.autonomous_retriever_agent import AutonomousRetrieverAgent
from src.agents.autonomous_rag_agent import AutonomousRAGAgent
from src.agents.autonomous_critic_agent import AutonomousCriticAgent

logger = logging.getLogger(__name__)


class AutonomousOrchestrator:
    """
    Orquestador Autónomo del Sistema Agentic AI.
    
    Coordina el flujo completo usando agentes autónomos que:
    - Toman sus propias decisiones
    - Usan tools cuando lo necesitan
    - Se comunican entre sí mediante sus outputs
    - Mantienen trazabilidad completa
    
    FLUJO DEL SISTEMA:
    
    1. **Usuario** → Consulta
    2. **ClassifierAgent** → Clasifica intención (busqueda/resumen/comparacion/general)
    3. **Decisión**:
       - Si general → RAGAgent genera respuesta directa
       - Si requiere RAG → Continuar flujo
    4. **RetrieverAgent** → Recupera documentos relevantes
    5. **RAGAgent** → Genera respuesta con contexto
    6. **CriticAgent** → Valida respuesta
    7. **Loop** (si necesario):
       - Si respuesta rechazada → RAGAgent regenera (máx 2 iteraciones)
    8. **Usuario** ← Respuesta final + trazabilidad
    
    CARACTERÍSTICAS:
    - Agentes completamente autónomos
    - Trazabilidad detallada de cada paso
    - Control de calidad con validación crítica
    - Loop de regeneración controlado
    - Manejo robusto de errores
    """
    
    def __init__(self):
        """
        Inicializa el orquestador y todos los agentes autónomos.
        
        Crea instancias de:
        - AutonomousClassifierAgent: Clasifica intenciones
        - AutonomousRetrieverAgent: Recupera documentos
        - AutonomousRAGAgent: Genera respuestas
        - AutonomousCriticAgent: Valida respuestas
        """
        logger.info("="*80)
        logger.info("Inicializando AutonomousOrchestrator con Agentes Autónomos")
        logger.info("="*80)
        
        self.start_time = datetime.now()
        
        # Inicializar agentes autónomos
        logger.info("\n[1/4] Inicializando ClassifierAgent...")
        self.classifier = AutonomousClassifierAgent()
        
        logger.info("\n[2/4] Inicializando RetrieverAgent...")
        self.retriever = AutonomousRetrieverAgent()
        
        logger.info("\n[3/4] Inicializando RAGAgent...")
        self.rag_agent = AutonomousRAGAgent()
        
        logger.info("\n[4/4] Inicializando CriticAgent...")
        self.critic = AutonomousCriticAgent()
        
        # Configuración
        self.max_regeneration_attempts = 2
        
        init_time = (datetime.now() - self.start_time).total_seconds()
        logger.info("="*80)
        logger.info(f"AutonomousOrchestrator inicializado en {init_time:.2f}s")
        logger.info("Sistema listo con 4 agentes autónomos + 11 tools")
        logger.info("="*80)
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Procesa una consulta del usuario de principio a fin.
        
        Ejecuta el flujo completo:
        1. Clasificación de intención
        2. Recuperación de documentos (si necesario)
        3. Generación de respuesta
        4. Validación crítica
        5. Regeneración (si necesario)
        
        Args:
            query: Consulta del usuario en lenguaje natural
            
        Returns:
            Diccionario con respuesta completa y trazabilidad:
            {
                "query": str,  # Consulta original
                "response": str,  # Respuesta final
                "intent": str,  # Intención clasificada
                "documents_used": int,  # Documentos recuperados
                "validation": Dict,  # Resultado de validación
                "trace": Dict,  # Trazabilidad completa del flujo
                "execution_time": float  # Tiempo total en segundos
            }
        """
        start_time = datetime.now()
        trace = {
            "steps": [],
            "agents_called": [],
            "tools_used": [],
            "regeneration_count": 0
        }
        
        logger.info("\n" + "="*80)
        logger.info(f"NUEVA CONSULTA: {query}")
        logger.info("="*80)
        
        try:
            # ===============================
            # PASO 1: CLASIFICACIÓN
            # ===============================
            logger.info("\n[PASO 1] Clasificando intención...")
            classification = self.classifier.classify(query)
            
            trace["steps"].append({
                "step": 1,
                "agent": "ClassifierAgent",
                "action": "Clasificar intención",
                "result": {
                    "intent": classification["intent"],
                    "confidence": classification["confidence"],
                    "requires_rag": classification["requires_rag"]
                }
            })
            trace["agents_called"].append("ClassifierAgent")
            
            intent = classification["intent"]
            requires_rag = classification["requires_rag"]
            
            logger.info(f"✓ Intención: {intent} | Confianza: {classification['confidence']:.2f} | RAG: {requires_rag}")
            
            # ===============================
            # DECISIÓN: ¿Requiere RAG?
            # ===============================
            if not requires_rag:
                logger.info("\n[DECISIÓN] No requiere RAG → Respuesta directa")
                
                # Generar respuesta general sin documentos
                generation_result = self.rag_agent.generate(
                    query=query,
                    documents=[],
                    intent=intent
                )
                
                trace["steps"].append({
                    "step": 2,
                    "agent": "RAGAgent",
                    "action": "Generar respuesta general",
                    "result": {"used_rag": False}
                })
                trace["agents_called"].append("RAGAgent")
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                logger.info("\n" + "="*80)
                logger.info(f"✓ CONSULTA COMPLETADA (sin RAG) en {execution_time:.2f}s")
                logger.info("="*80)
                
                return {
                    "query": query,
                    "response": generation_result["response"],
                    "intent": intent,
                    "documents_used": 0,
                    "validation": {"is_valid": True, "confidence_score": 1.0},
                    "trace": trace,
                    "execution_time": execution_time
                }
            
            # ===============================
            # PASO 2: RECUPERACIÓN
            # ===============================
            logger.info("\n[PASO 2] Recuperando documentos...")
            retrieval_result = self.retriever.retrieve(
                query=query,
                intent=intent
            )
            
            documents = retrieval_result["documents"]
            
            trace["steps"].append({
                "step": 2,
                "agent": "RetrieverAgent",
                "action": "Recuperar documentos",
                "result": {
                    "documents_found": len(documents),
                    "query_used": retrieval_result["query_used"]
                }
            })
            trace["agents_called"].append("RetrieverAgent")
            
            logger.info(f"✓ Recuperados: {len(documents)} documentos")
            
            if len(documents) == 0:
                logger.warning("⚠ No se encontraron documentos relevantes")
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return {
                    "query": query,
                    "response": "No se encontraron documentos relevantes para responder tu consulta.",
                    "intent": intent,
                    "documents_used": 0,
                    "validation": {"is_valid": True, "confidence_score": 1.0},
                    "trace": trace,
                    "execution_time": execution_time
                }
            
            # ===============================
            # PASO 3: GENERACIÓN (con loop)
            # ===============================
            response_text = None
            validation_result = None
            generation_attempt = 0
            
            while generation_attempt < self.max_regeneration_attempts:
                generation_attempt += 1
                
                logger.info(f"\n[PASO 3.{generation_attempt}] Generando respuesta...")
                
                generation_result = self.rag_agent.generate(
                    query=query,
                    documents=documents,
                    intent=intent
                )
                
                response_text = generation_result["response"]
                
                trace["steps"].append({
                    "step": f"3.{generation_attempt}",
                    "agent": "RAGAgent",
                    "action": f"Generar respuesta (intento {generation_attempt})",
                    "result": {
                        "used_rag": generation_result["used_rag"],
                        "response_length": len(response_text)
                    }
                })
                trace["agents_called"].append("RAGAgent")
                
                logger.info(f"✓ Respuesta generada ({len(response_text)} caracteres)")
                
                # ===============================
                # PASO 4: VALIDACIÓN
                # ===============================
                logger.info(f"\n[PASO 4.{generation_attempt}] Validando respuesta...")
                
                validation_result = self.critic.validate(
                    query=query,
                    response=response_text,
                    context_documents=documents
                )
                
                trace["steps"].append({
                    "step": f"4.{generation_attempt}",
                    "agent": "CriticAgent",
                    "action": "Validar respuesta",
                    "result": {
                        "is_valid": validation_result["is_valid"],
                        "confidence_score": validation_result["confidence_score"],
                        "needs_regeneration": validation_result["needs_regeneration"]
                    }
                })
                trace["agents_called"].append("CriticAgent")
                
                logger.info(f"✓ Validación: valid={validation_result['is_valid']}, "
                          f"score={validation_result['confidence_score']:.2f}, "
                          f"regenerate={validation_result['needs_regeneration']}")
                
                # Decidir si regenerar
                if not validation_result["needs_regeneration"]:
                    logger.info("✓ Respuesta APROBADA")
                    break
                else:
                    logger.warning(f"⚠ Respuesta RECHAZADA - Problemas: {validation_result['issues']}")
                    trace["regeneration_count"] += 1
                    
                    if generation_attempt >= self.max_regeneration_attempts:
                        logger.warning(f"⚠ Máximo de regeneraciones alcanzado ({self.max_regeneration_attempts})")
                        logger.warning("Devolviendo última respuesta generada a pesar de validación")
                        break
                    else:
                        logger.info(f"→ Regenerando respuesta (intento {generation_attempt + 1}/{self.max_regeneration_attempts})")
            
            # ===============================
            # RESULTADO FINAL
            # ===============================
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.info("\n" + "="*80)
            logger.info(f"✓ CONSULTA COMPLETADA en {execution_time:.2f}s")
            logger.info(f"  - Intención: {intent}")
            logger.info(f"  - Documentos: {len(documents)}")
            logger.info(f"  - Regeneraciones: {trace['regeneration_count']}")
            logger.info(f"  - Validación: {validation_result['confidence_score']:.2f}")
            logger.info("="*80)
            
            # Extraer tools usadas del trace
            for step in trace["steps"]:
                if "intermediate_steps" in step.get("result", {}):
                    for istep in step["result"]["intermediate_steps"]:
                        if "tool" in istep:
                            tool_name = istep["tool"]
                            if tool_name not in trace["tools_used"]:
                                trace["tools_used"].append(tool_name)
            
            return {
                "query": query,
                "response": response_text,
                "intent": intent,
                "documents_used": len(documents),
                "validation": validation_result,
                "trace": trace,
                "execution_time": execution_time
            }
            
        except Exception as e:
            logger.error(f"\n✗ ERROR en orquestación: {str(e)}", exc_info=True)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "query": query,
                "response": f"Lo siento, hubo un error al procesar tu consulta: {str(e)}",
                "intent": "error",
                "documents_used": 0,
                "validation": {"is_valid": False, "confidence_score": 0.0},
                "trace": trace,
                "execution_time": execution_time,
                "error": str(e)
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre el estado del sistema.
        
        Returns:
            Diccionario con información del sistema:
            {
                "agents": int,
                "tools_available": int,
                "status": str
            }
        """
        return {
            "agents": 4,
            "tools_available": 11,
            "status": "operational",
            "autonomous": True,
            "max_regenerations": self.max_regeneration_attempts
        }
