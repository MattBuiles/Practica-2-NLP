"""
Agente Recuperador Autónomo con Tools.
Busca y optimiza la recuperación de documentos de forma inteligente.
"""
import logging
import time
from typing import Dict, Any, List
from langchain.agents import create_agent
from pydantic import BaseModel, Field

from src.config.llm_config import llm_config
from src.tools import RETRIEVER_TOOLS

logger = logging.getLogger(__name__)

# Delay entre llamadas API para evitar rate limiting
API_DELAY = 1.5


class RetrievalResult(BaseModel):
    """Modelo de salida estructurada para resultado de recuperación."""
    documents: List[Dict[str, Any]] = Field(description="Lista de documentos recuperados")
    query_used: str = Field(description="Query utilizada para la búsqueda")
    num_documents: int = Field(description="Número de documentos encontrados")
    optimized: bool = Field(description="Si la query fue optimizada")


class AutonomousRetrieverAgent:
    """
    Agente Recuperador Autónomo basado en LangChain.
    
    Este agente gestiona la recuperación de documentos de forma inteligente:
    - Decide si optimizar la query antes de buscar
    - Determina cuántos documentos recuperar según contexto
    - Puede hacer múltiples búsquedas si es necesario
    - Filtra resultados por relevancia
    - Registra todas sus acciones
    
    TOOLS DISPONIBLES:
    - search_documents: Buscar documentos por similitud semántica
    - search_documents_by_metadata: Buscar por filtros específicos
    - optimize_search_query: Optimizar query para mejor recuperación
    - log_agent_action: Registrar acciones ejecutadas
    
    CAPACIDADES:
    - Búsqueda semántica optimizada
    - Estrategias adaptativas según intención
    - Filtrado inteligente de resultados
    - Manejo de búsquedas complejas (comparación, resumen)
    """
    
    def __init__(self):
        """
        Inicializa el agente recuperador autónomo.
        
        Configura:
        - LLM rápido para decisiones (Groq)
        - Tools de búsqueda y optimización
        - Prompt con estrategias de recuperación
        - AgentExecutor para autonomía
        """
        logger.info("Inicializando AutonomousRetrieverAgent...")
        
        # LLM rápido para recuperación (Groq)
        self.llm = llm_config.get_retriever_llm()
        
        # Tools disponibles
        self.tools = RETRIEVER_TOOLS
        
        # Crear prompt del sistema
        self.system_prompt = self._create_system_prompt()
        
        # Crear agente con langchain (retorna un grafo ejecutable)
        self.agent_executor = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt
        )
        
        logger.info(f"AutonomousRetrieverAgent inicializado con {len(self.tools)} tools")
    
    def _create_system_prompt(self) -> str:
        """Crea el prompt del sistema para el agente recuperador."""
        return """Eres un Agente Recuperador Autónomo experto en búsqueda semántica.

TU MISIÓN:
Recuperar los documentos más relevantes para responder la consulta del usuario.
USA SIEMPRE LA QUERY EXACTA QUE TE DAN - NO la reemplaces con ejemplos.

HERRAMIENTAS DISPONIBLES:
- search_documents(query, k, score_threshold): Busca documentos por similitud
  - query: USA LA QUERY EXACTA DEL USUARIO, no ejemplos
  - k: Número de documentos (3-10 según contexto)
  - score_threshold: Umbral de relevancia (0.0 = todos)

- optimize_search_query(query, intent): Optimiza la query para mejor recuperación
  - USA LA QUERY DEL USUARIO como entrada
  - Expande con sinónimos y términos relacionados

- search_documents_by_metadata(metadata_filter, k): Busca por filtros específicos

- log_agent_action: Registra tus acciones

ESTRATEGIA DE RECUPERACIÓN:

1. **PARA BÚSQUEDA SIMPLE** (intent="busqueda"):
   - USA LA QUERY EXACTA del usuario
   - Recupera 4-5 documentos
   - Usa score_threshold=0.0

2. **PARA RESUMEN** (intent="resumen"):
   - USA LA QUERY del usuario, puedes optimizarla
   - Recupera 8-10 documentos
   - Usa score_threshold=0.0

3. **PARA COMPARACIÓN** (intent="comparacion"):
   - USA LA QUERY del usuario
   - Recupera 5-6 documentos
   - Asegura balance entre conceptos

IMPORTANTE:
- SIEMPRE usa la query que recibes del usuario
- NUNCA uses ejemplos como query de búsqueda
- La query viene en el mensaje del usuario, úsala directamente

INSTRUCCIÓN CRÍTICA:
Cuando recibas una query como "Busca documentos para: ¿Cuáles fueron los dinosaurios más grandes?"
DEBES buscar exactamente "¿Cuáles fueron los dinosaurios más grandes?" - NO otros términos.

FORMATO DE RESPUESTA FINAL:
Después de recuperar documentos, responde:
"He recuperado [N] documentos relevantes."

IMPORTANTE:
- USA LA QUERY EXACTA del usuario, no inventes otra
- Sé eficiente: no hagas más búsquedas de las necesarias
- Adapta k según la intención"""
    
    def retrieve(self, query: str, intent: str = "busqueda", k: int = None) -> Dict[str, Any]:
        """
        Recupera documentos de forma autónoma.
        
        El agente:
        1. Analiza la query y la intención
        2. Decide si optimizar la query
        3. Determina cuántos documentos recuperar
        4. Ejecuta búsqueda(s)
        5. Registra sus acciones
        6. Retorna documentos recuperados
        
        Args:
            query: Consulta de búsqueda
            intent: Tipo de intención (busqueda, resumen, comparacion)
            k: Número de documentos (opcional, el agente decide si no se proporciona)
            
        Returns:
            Diccionario con documentos recuperados y metadatos:
            {
                "documents": List[Dict],  # Documentos encontrados
                "query_used": str,  # Query final usada
                "count": int,  # Número de documentos
                "intermediate_steps": list  # Acciones del agente
            }
        """
        try:
            logger.info(f"[AutonomousRetriever] Query: '{query[:80]}', intent: {intent}")
            
            # Delay para evitar rate limiting
            time.sleep(API_DELAY)
            
            # Preparar mensaje para el agente - enfatizar la query real
            if k is not None:
                user_message = f"""BUSCA DOCUMENTOS PARA ESTA QUERY EXACTA:
Query: {query}
Intención: {intent}
Número de documentos requeridos: {k}

USA EXACTAMENTE la query "{query}" para buscar, no otra."""
            else:
                user_message = f"""BUSCA DOCUMENTOS PARA ESTA QUERY EXACTA:
Query: {query}
Intención: {intent}

USA EXACTAMENTE la query "{query}" para buscar, no otra."""
            
            # Invocar agente con formato LangChain 1.1
            result = self.agent_executor.invoke({
                "messages": [
                    {"role": "user", "content": user_message}
                ]
            })
            
            # Extraer documentos del nuevo formato de mensajes
            messages = result.get("messages", [])
            documents = []
            tool_calls = []
            
            for msg in messages:
                # Procesar AIMessage con tool_calls
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tool_calls.extend(msg.tool_calls)
                # Procesar ToolMessage (resultados de búsqueda)
                elif hasattr(msg, 'tool_call_id') and hasattr(msg, 'content'):
                    try:
                        import json
                        tool_result = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                        # Si es una lista de documentos, agregarlos
                        if isinstance(tool_result, list):
                            documents.extend(tool_result)
                        elif isinstance(tool_result, dict) and 'documents' in tool_result:
                            documents.extend(tool_result['documents'])
                    except json.JSONDecodeError:
                        pass
                    except Exception:
                        pass
            
            logger.info(f"[AutonomousRetriever] Recuperados {len(documents)} documentos")
            
            return {
                "documents": documents,
                "query_used": query,
                "count": len(documents),
                "intermediate_steps": [
                    {
                        "tool": tc.get("name", "unknown") if isinstance(tc, dict) else getattr(tc, 'name', 'unknown'),
                        "input": str(tc.get("args", {}) if isinstance(tc, dict) else getattr(tc, 'args', {}))[:100]
                    }
                    for tc in tool_calls
                ]
            }
            
        except Exception as e:
            logger.error(f"[AutonomousRetriever] Error: {str(e)}")
            return {
                "documents": [],
                "query_used": query,
                "count": 0,
                "error": str(e),
                "intermediate_steps": []
            }
