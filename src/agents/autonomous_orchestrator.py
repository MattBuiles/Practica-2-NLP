"""
Orquestador Autónomo con Agentes y Tools.
Coordina el flujo completo del sistema usando agentes autónomos con decisiones LLM.
"""
import logging
import time
import json
import re
from typing import Dict, Any
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.agents.autonomous_classifier_agent import AutonomousClassifierAgent
from src.agents.autonomous_retriever_agent import AutonomousRetrieverAgent
from src.agents.autonomous_rag_agent import AutonomousRAGAgent
from src.agents.autonomous_critic_agent import AutonomousCriticAgent
from src.config.llm_config import llm_config
from src.rag_pipeline.vectorstore import vectorstore_manager

# Delay entre llamadas API para evitar rate limiting
API_DELAY = 1.5  # segundos

logger = logging.getLogger(__name__)


class OrchestrationDecision(BaseModel):
    """Decisión del orquestador sobre cómo procesar la consulta."""
    strategy: str = Field(description="Estrategia a seguir: direct_response, simple_rag, comparison_rag, summary_rag, multi_hop")
    num_documents: int = Field(description="Número de documentos a recuperar (0 si no aplica)")
    retrieval_mode: str = Field(description="Modo de recuperación: standard, comparison, summary, none")
    needs_validation: bool = Field(description="Si requiere validación crítica")
    reasoning: str = Field(description="Justificación de la decisión")


class AutonomousOrchestrator:
    """
    Orquestador Autónomo del Sistema Agentic AI.
    
    Usa LLM (Groq) para tomar decisiones inteligentes sobre:
    - Estrategia de procesamiento óptima
    - Número de documentos a recuperar
    - Modo de recuperación según contexto
    - Necesidad de validación crítica
    
    Coordina agentes autónomos que:
    - Toman sus propias decisiones
    - Usan tools cuando lo necesitan
    - Se comunican entre sí mediante sus outputs
    - Mantienen trazabilidad completa
    
    FLUJO DEL SISTEMA:
    
    1. **Usuario** → Consulta
    2. **ClassifierAgent** → Clasifica intención (busqueda/resumen/comparacion/general)
    3. **Orchestrator LLM** → Decide estrategia óptima con salida estructurada
    4. **Decisión basada en estrategia**:
       - direct_response → RAGAgent responde directamente
       - simple_rag/comparison_rag/summary_rag → Flujo RAG completo
    5. **RetrieverAgent** → Recupera N documentos (según decisión LLM)
    6. **RAGAgent** → Genera respuesta con contexto
    7. **CriticAgent** → Valida (solo si needs_validation=true)
    8. **Loop** (si necesario):
       - Si respuesta rechazada → RAGAgent regenera (máx 2 iteraciones)
    9. **Usuario** ← Respuesta final + trazabilidad
    """
    
    def __init__(self):
        """
        Inicializa el orquestador y todos los agentes autónomos.
        
        Crea instancias de:
        - AutonomousClassifierAgent: Clasifica intenciones con tools
        - AutonomousRetrieverAgent: Recupera documentos con tools
        - AutonomousRAGAgent: Genera respuestas con tools
        - AutonomousCriticAgent: Valida respuestas con tools
        - LLM de Orquestación: Decide estrategias con salida estructurada
        """
        logger.info("="*80)
        logger.info("Inicializando AutonomousOrchestrator con LLM de Decisión")
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
        
        # Cargar vectorstore
        logger.info("\n[5/6] Cargando vector store...")
        try:
            vectorstore_manager.load_index()
            if vectorstore_manager.vectorstore:
                stats = vectorstore_manager.get_index_stats()
                logger.info(f"✓ Vector store cargado: {stats.get('documents', 0)} documentos")
            else:
                logger.warning("⚠ Vector store no pudo cargarse - el sistema funcionará pero sin RAG")
        except Exception as e:
            logger.warning(f"⚠ Error cargando vector store: {e}")
        
        # LLM para decisiones de orquestación (SIN structured_output por incompatibilidad con Groq)
        logger.info("\n[6/6] Configurando LLM de Orquestación...")
        self.llm = llm_config.get_orchestrator_llm()
        # NO usar structured_output - Groq devuelve strings en vez de tipos correctos
        # self.structured_llm = self.llm.with_structured_output(OrchestrationDecision)
        
        # Prompt para decisiones - ahora pide JSON explícito
        self.decision_prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_decision_prompt()),
            ("user", "Consulta: {query}\nIntención: {intent}\nConfianza: {confidence}\nRequiere RAG: {requires_rag}")
        ])
        
        # Configuración
        self.max_regeneration_attempts = 2
        
        init_time = (datetime.now() - self.start_time).total_seconds()
        logger.info("="*80)
        logger.info(f"AutonomousOrchestrator inicializado en {init_time:.2f}s")
        logger.info("Sistema listo: 4 agentes autónomos + LLM decisor + Vector Store")
        logger.info("="*80)
    
    def _get_decision_prompt(self) -> str:
        """Genera el prompt para decisiones de orquestación."""
        return """Eres un orquestador experto de sistemas RAG. Tu tarea es decidir la mejor estrategia para procesar consultas.

RESPONDE ÚNICAMENTE CON UN JSON VÁLIDO (sin markdown, sin explicaciones):

{
  "strategy": "simple_rag",
  "num_documents": 5,
  "retrieval_mode": "standard",
  "needs_validation": true,
  "reasoning": "Explicación breve"
}

VALORES PERMITIDOS:
- strategy: "direct_response", "simple_rag", "comparison_rag", "summary_rag", "multi_hop"
- num_documents: 0, 3, 4, 5, 6, 8, 10 (número entero)
- retrieval_mode: "none", "standard", "comparison", "summary"
- needs_validation: true o false (booleano, NO string)

ESTRATEGIAS:
1. direct_response: Sin RAG (saludos, charla) → num_documents=0, retrieval_mode="none", needs_validation=false
2. simple_rag: Búsqueda de información → num_documents=5, retrieval_mode="standard", needs_validation=true
3. comparison_rag: Comparar conceptos → num_documents=6, retrieval_mode="comparison", needs_validation=true
4. summary_rag: Resumir documentos → num_documents=8, retrieval_mode="summary", needs_validation=true
5. multi_hop: Preguntas complejas → num_documents=6, retrieval_mode="standard", needs_validation=true

SOLO RESPONDE CON EL JSON, NADA MÁS."""
    
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parsea respuesta JSON del LLM con enfoque simple y robusto."""
        # 1. Limpiar markdown
        text = text.replace('```json', '').replace('```', '').strip()
        
        # 2. Encontrar el JSON entre { y }
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = text[start_idx:end_idx + 1]
            
            # Normalizar: colapsar todos los espacios y newlines
            json_str = ' '.join(json_str.split())
            
            try:
                data = json.loads(json_str)
                
                # Extraer y validar strategy
                strategy = str(data.get('strategy', 'simple_rag')).lower().strip()
                valid_strategies = ["direct_response", "simple_rag", "comparison_rag", "summary_rag", "multi_hop"]
                if strategy not in valid_strategies:
                    strategy = "simple_rag"
                
                # Extraer num_documents
                num_docs = data.get('num_documents', 5)
                if isinstance(num_docs, str):
                    try:
                        num_docs = int(num_docs)
                    except:
                        num_docs = 5
                
                # Extraer retrieval_mode
                mode = str(data.get('retrieval_mode', 'standard'))
                
                # Extraer needs_validation
                needs_val = data.get('needs_validation', True)
                if isinstance(needs_val, str):
                    needs_val = needs_val.lower() in ['true', '1', 'yes', 'si']
                
                # Extraer reasoning
                reasoning = str(data.get('reasoning', 'Estrategia automática'))
                
                return {
                    "strategy": strategy,
                    "num_documents": int(num_docs),
                    "retrieval_mode": mode,
                    "needs_validation": bool(needs_val),
                    "reasoning": reasoning
                }
                
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON inválido: {e}")
        
        raise ValueError(f"No se encontró JSON en: {text[:100]}")
    
    def _decide_strategy(self, query: str, classification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Usa LLM para decidir la estrategia óptima de procesamiento.
        Parsea JSON manualmente en lugar de usar structured_output.
        """
        try:
            logger.info("→ Usando LLM para decidir estrategia de orquestación...")
            
            # Delay para evitar rate limiting
            time.sleep(API_DELAY)
            
            messages = self.decision_prompt.format_messages(
                query=query,
                intent=classification["intent"],
                confidence=classification["confidence"],
                requires_rag=classification["requires_rag"]
            )
            
            response = self.llm.invoke(messages)
            decision = self._parse_json_response(response.content)
            
            result = {
                "strategy": decision.get("strategy", "simple_rag"),
                "num_documents": int(decision.get("num_documents", 5)),
                "retrieval_mode": decision.get("retrieval_mode", "standard"),
                "needs_validation": bool(decision.get("needs_validation", True)),
                "reasoning": decision.get("reasoning", "Sin razonamiento")
            }
            
            logger.info(f"✓ Estrategia: {result['strategy']} | Docs: {result['num_documents']} | Validar: {result['needs_validation']}")
            logger.info(f"  Razonamiento: {result['reasoning'][:150]}...")
            return result
            
        except Exception as e:
            logger.error(f"✗ Error en decisión LLM: {str(e)}")
            logger.warning("→ Usando fallback basado en clasificación")
            
            # Fallback basado en clasificación
            intent = classification["intent"]
            requires_rag = classification["requires_rag"]
            
            if not requires_rag:
                strategy = "direct_response"
                num_docs = 0
                mode = "none"
            elif intent == "comparacion":
                strategy = "comparison_rag"
                num_docs = 5
                mode = "comparison"
            elif intent == "resumen":
                strategy = "summary_rag"
                num_docs = 8
                mode = "summary"
            else:
                strategy = "simple_rag"
                num_docs = 5
                mode = "standard"
            
            return {
                "strategy": strategy,
                "num_documents": num_docs,
                "retrieval_mode": mode,
                "needs_validation": requires_rag,
                "reasoning": f"Fallback basado en clasificación: {intent}"
            }
    
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
            # PASO 2: DECISIÓN DE ESTRATEGIA CON LLM
            # ===============================
            logger.info("\n[PASO 2] Decidiendo estrategia con LLM...")
            decision = self._decide_strategy(query, classification)
            
            trace["steps"].append({
                "step": 2,
                "agent": "OrchestratorLLM",
                "action": "Decidir estrategia",
                "result": {
                    "strategy": decision["strategy"],
                    "num_documents": decision["num_documents"],
                    "retrieval_mode": decision["retrieval_mode"],
                    "needs_validation": decision["needs_validation"],
                    "reasoning": decision["reasoning"]
                }
            })
            trace["agents_called"].append("OrchestratorLLM")
            
            logger.info(f"✓ Estrategia: {decision['strategy']} | Documentos: {decision['num_documents']} | Modo: {decision['retrieval_mode']}")
            
            # ===============================
            # DECISIÓN: Ejecutar según estrategia
            # ===============================
            if decision["strategy"] == "direct_response":
                logger.info("\n[DECISIÓN] Estrategia: direct_response → Sin RAG")
                logger.info("\n[DECISIÓN] Estrategia: direct_response → Sin RAG")
                
                # Respuesta directa usando RAGAgent (sin contexto documental)
                #TODO ACTUALIZAR A USAR CLASSIFIER
                generation_result = self.rag_agent.generate(
                    query=query,
                    documents=[],
                    intent=intent
                )
                
                response_text = generation_result["response"]
                
                trace["steps"].append({
                    "step": 3,
                    "agent": "RAGAgent",
                    "action": "Responder consulta general directamente",
                    "result": {"used_rag": False, "response_length": len(response_text)}
                })
                trace["agents_called"].append("RAGAgent")
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                logger.info("\n" + "="*80)
                logger.info(f"✓ CONSULTA COMPLETADA (sin RAG) en {execution_time:.2f}s")
                logger.info(f"  - Estrategia: {decision['strategy']}")
                logger.info(f"  - Respondida directamente por RAGAgent")
                logger.info("="*80)
                
                return {
                    "query": query,
                    "response": response_text,
                    "intent": intent,
                    "strategy": decision["strategy"],
                    "documents_used": 0,
                    "validation": {"is_valid": True, "confidence_score": 1.0},
                    "trace": trace,
                    "execution_time": execution_time
                }
            
            # ===============================
            # PASO 3: RECUPERACIÓN (según modo decidido)
            # ===============================
            logger.info(f"\n[PASO 3] Recuperando {decision['num_documents']} documentos (modo: {decision['retrieval_mode']})...")
            
            retrieval_result = self.retriever.retrieve(
                query=query,
                intent=intent,
                k=decision['num_documents']
            )
            
            documents = retrieval_result["documents"]
            
            trace["steps"].append({
                "step": 3,
                "agent": "RetrieverAgent",
                "action": f"Recuperar documentos ({decision['retrieval_mode']})",
                "result": {
                    "documents_found": len(documents),
                    "query_used": retrieval_result["query_used"],
                    "strategy_requested": decision["num_documents"]
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
                    "strategy": decision["strategy"],
                    "documents_used": 0,
                    "validation": {"is_valid": True, "confidence_score": 1.0},
                    "trace": trace,
                    "execution_time": execution_time
                }
            
            # ===============================
            # PASO 4: GENERACIÓN (con loop de regeneración)
            # ===============================
            response_text = None
            validation_result = None
            generation_attempt = 0
            
            while generation_attempt < self.max_regeneration_attempts:
                generation_attempt += 1
                
                logger.info(f"\n[PASO 4.{generation_attempt}] Generando respuesta...")
                
                generation_result = self.rag_agent.generate(
                    query=query,
                    documents=documents,
                    intent=intent
                )
                
                response_text = generation_result["response"]
                
                trace["steps"].append({
                    "step": f"4.{generation_attempt}",
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
                # PASO 5: VALIDACIÓN (solo si la estrategia lo requiere)
                # ===============================
                if decision["needs_validation"]:
                    logger.info(f"\n[PASO 5.{generation_attempt}] Validando respuesta...")
                    
                    validation_result = self.critic.validate(
                        query=query,
                        response=response_text,
                        context_documents=documents
                    )
                    
                    trace["steps"].append({
                        "step": f"5.{generation_attempt}",
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
                else:
                    # Validación omitida por estrategia
                    logger.info(f"\n[PASO 5.{generation_attempt}] Validación OMITIDA (estrategia: {decision['strategy']})")
                    validation_result = {
                        "is_valid": True,
                        "confidence_score": 1.0,
                        "needs_regeneration": False,
                        "issues": [],
                        "skipped": True
                    }
                    break  # No loop si no hay validación
            
            # ===============================
            # RESULTADO FINAL
            # ===============================
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.info("\n" + "="*80)
            logger.info(f"✓ CONSULTA COMPLETADA en {execution_time:.2f}s")
            logger.info(f"  - Intención: {intent}")
            logger.info(f"  - Estrategia: {decision['strategy']}")
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
                "strategy": decision["strategy"],
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
                "strategy": "error",
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
