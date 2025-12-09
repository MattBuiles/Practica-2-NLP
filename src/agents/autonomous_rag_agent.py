"""
Agente RAG Autónomo con Tools.
Genera respuestas basadas en contexto de forma inteligente y adaptativa.
"""
import logging
from typing import Dict, Any, List
from langchain.agents import create_agent

from src.config.llm_config import llm_config
from src.tools import RAG_TOOLS

logger = logging.getLogger(__name__)


class AutonomousRAGAgent:
    """
    Agente RAG Autónomo basado en LangChain.
    
    Este agente genera respuestas de forma inteligente:
    - Decide si usar RAG o respuesta general según contexto
    - Adapta el estilo de respuesta a la intención (búsqueda, resumen, comparación)
    - Puede solicitar más documentos si la información es insuficiente
    - Verifica la calidad de su propia respuesta
    - Registra el proceso de generación
    
    TOOLS DISPONIBLES:
    - generate_rag_response: Generar respuesta con documentos (RAG)
    - generate_general_response: Generar respuesta sin documentos
    - log_agent_action: Registrar acciones
    
    CAPACIDADES:
    - Generación contextual con citas
    - Adaptación a diferentes intenciones
    - Respuestas generales sin RAG
    - Auto-evaluación de calidad
    """
    
    def __init__(self):
        """
        Inicializa el agente RAG autónomo.
        
        Configura:
        - LLM rápido para generación (Groq)
        - Tools de generación
        - Prompt con estrategias por intención
        - AgentExecutor para autonomía
        """
        logger.info("Inicializando AutonomousRAGAgent...")
        
        # LLM rápido para generación (Groq)
        self.llm = llm_config.get_rag_llm()
        
        # Tools disponibles
        self.tools = RAG_TOOLS
        
        # Prompt del sistema
        self.system_prompt = self._create_system_prompt()
        
        # Crear agente con langchain (retorna un grafo ejecutable)
        self.agent_executor = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt
        )
        
        logger.info(f"AutonomousRAGAgent inicializado con {len(self.tools)} tools")
    
    def _create_system_prompt(self) -> str:
        """Crea el prompt del sistema para el agente RAG."""
        return """Eres un Agente RAG Autónomo experto en generación de respuestas contextuales.

TU MISIÓN:
Generar una respuesta apropiada para la consulta del usuario, usando documentos si están disponibles.

HERRAMIENTAS DISPONIBLES:

1. generate_rag_response(query, documents, intent):
   - Genera respuesta basada en documentos recuperados
   - Incluye citas automáticamente
   - Adapta estilo según intent (busqueda/resumen/comparacion)
   - Usa SIEMPRE que tengas documentos disponibles

2. generate_general_response(query):
   - Genera respuesta sin documentos (conversacional)
   - Para consultas generales (saludos, charla)
   - Usa SOLO cuando intent="general" y no hay documentos

3. log_agent_action(agent_name, action, input_data, output_data):
   - Registra tus acciones para trazabilidad

ESTRATEGIA DE GENERACIÓN:

1. **SI intent="general" y NO hay documentos**:
   → Usa generate_general_response
   → Responde de forma conversacional y amigable

2. **SI intent="busqueda" y HAY documentos**:
   → Usa generate_rag_response con intent="busqueda"
   → Respuesta directa, precisa, con citas
   → Enfoque: responder la pregunta específica

3. **SI intent="resumen" y HAY documentos**:
   → Usa generate_rag_response con intent="resumen"
   → Síntesis estructurada de puntos clave
   → Organiza con viñetas o numeración
   → Enfoque: capturar información principal

4. **SI intent="comparacion" y HAY documentos**:
   → Usa generate_rag_response con intent="comparacion"
   → Análisis contrastivo punto por punto
   → Destaca similitudes y diferencias
   → Enfoque: comparación objetiva

FORMATO DE DOCUMENTOS:
Los documentos vienen como lista:
[
  {{"content": "...", "metadata": {{"source": "..."}}}}
]

Para usar generate_rag_response, pasa la lista completa.

EJEMPLOS:

Ejemplo 1 - Búsqueda con documentos:
Input: query="¿Qué es la diabetes?", documents=[...5 docs...], intent="busqueda"
Acción:
1. generate_rag_response(
     query="¿Qué es la diabetes?",
     documents=documents,
     intent="busqueda"
   )
2. log_agent_action(...)

Ejemplo 2 - Consulta general sin documentos:
Input: query="Hola, ¿cómo estás?", documents=[], intent="general"
Acción:
1. generate_general_response("Hola, ¿cómo estás?")
2. log_agent_action(...)

Ejemplo 3 - Resumen con documentos:
Input: query="Resume info sobre COVID", documents=[...10 docs...], intent="resumen"
Acción:
1. generate_rag_response(
     query="Resume info sobre COVID",
     documents=documents,
     intent="resumen"
   )
2. log_agent_action(...)

CALIDAD DE RESPUESTA:
- Usa toda la información relevante de los documentos
- Siempre incluye citas cuando uses documentos
- Sé preciso y no inventes información
- Adapta el tono según la intención

FORMATO DE SALIDA:
Simplemente devuelve la respuesta generada por la tool que uses.
No agregues texto adicional, la respuesta de la tool ES tu respuesta final.

IMPORTANTE:
- NO generes respuestas manualmente, USA las tools
- Elige la tool correcta según intent y disponibilidad de documentos
- Registra siempre tus acciones
- Las tools ya manejan citas y formato"""
    
    def generate(self, query: str, documents: List[Dict[str, Any]], intent: str = "busqueda") -> Dict[str, Any]:
        """
        Genera respuesta de forma autónoma.
        
        El agente:
        1. Analiza query, documentos e intención
        2. Decide qué tool usar (RAG o general)
        3. Genera respuesta con estilo apropiado
        4. Registra la acción
        5. Retorna respuesta y metadata
        
        Args:
            query: Consulta del usuario
            documents: Documentos recuperados (puede ser vacío)
            intent: Tipo de intención (busqueda, resumen, comparacion, general)
            
        Returns:
            Diccionario con respuesta generada:
            {
                "response": str,  # Respuesta generada
                "used_rag": bool,  # Si usó RAG o respuesta general
                "num_documents": int,  # Documentos usados
                "intermediate_steps": list  # Acciones del agente
            }
        """
        try:
            logger.info(f"[AutonomousRAG] Query: '{query[:80]}', docs: {len(documents)}, intent: {intent}")
            
            # Preparar input para el agente
            # IMPORTANTE: Pasar documentos como contexto, no en el input string
            agent_input = {
                "query": query,
                "intent": intent,
                "num_documents": len(documents),
                "input": f"Query: {query}\nIntent: {intent}\nDocumentos disponibles: {len(documents)}"
            }
            
            # Ejecutar agente
            # Nota: Las tools recibirán los documentos directamente cuando las invoquen
            result = self.agent_executor.invoke(agent_input)
            
            # Extraer respuesta
            response_text = result.get("output", "")
            steps = result.get("intermediate_steps", [])
            
            # Determinar si usó RAG
            used_rag = any(
                hasattr(step[0], 'tool') and 'rag_response' in step[0].tool
                for step in steps
            )
            
            # Si las tools no se ejecutaron correctamente, extraer respuesta de los steps
            if not response_text and steps:
                for step in steps:
                    if isinstance(step[1], str) and len(step[1]) > 50:
                        response_text = step[1]
                        break
            
            logger.info(f"[AutonomousRAG] Respuesta generada ({len(response_text)} chars), RAG={used_rag}")
            
            return {
                "response": response_text,
                "used_rag": used_rag,
                "num_documents": len(documents),
                "intermediate_steps": [
                    {
                        "tool": step[0].tool if hasattr(step[0], 'tool') else "reasoning",
                        "preview": str(step[1])[:200]
                    }
                    for step in steps
                ]
            }
            
        except Exception as e:
            logger.error(f"[AutonomousRAG] Error: {str(e)}")
            
            # Fallback: generar respuesta básica
            if documents and intent != "general":
                fallback = f"Encontré {len(documents)} documentos relevantes, pero hubo un error al procesar la respuesta: {str(e)}"
            else:
                fallback = f"Disculpa, hubo un error al generar la respuesta: {str(e)}"
            
            return {
                "response": fallback,
                "used_rag": False,
                "num_documents": len(documents),
                "error": str(e),
                "intermediate_steps": []
            }
