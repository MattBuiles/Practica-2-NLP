"""
Agente Recuperador Autónomo con Tools.
Busca y optimiza la recuperación de documentos de forma inteligente.
"""
import logging
from typing import Dict, Any, List
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate

from src.config.llm_config import llm_config
from src.tools import RETRIEVER_TOOLS

logger = logging.getLogger(__name__)


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
        
        # Prompt del sistema
        self.prompt = self._create_agent_prompt()
        
        # Crear agente con langgraph (retorna un grafo ejecutable)
        self.agent_executor = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        logger.info(f"AutonomousRetrieverAgent inicializado con {len(self.tools)} tools")
    
    def _create_agent_prompt(self) -> ChatPromptTemplate:
        """Crea el prompt del sistema para el agente recuperador."""
        return ChatPromptTemplate.from_messages([
            ("system", """Eres un Agente Recuperador Autónomo experto en búsqueda semántica.

TU MISIÓN:
Recuperar los documentos más relevantes para responder la consulta del usuario.

HERRAMIENTAS DISPONIBLES:
- search_documents(query, k, score_threshold): Busca documentos por similitud
  - query: La consulta de búsqueda
  - k: Número de documentos (3-10 según contexto)
  - score_threshold: Umbral de relevancia (0.0 = todos, 0.5+ = solo muy relevantes)

- optimize_search_query(query, intent): Optimiza la query para mejor recuperación
  - Expande con sinónimos y términos relacionados
  - Mejora queries vagas o cortas

- search_documents_by_metadata(metadata_filter, k): Busca por filtros específicos
  - Útil cuando el usuario menciona un documento concreto

- log_agent_action: Registra tus acciones

ESTRATEGIA DE RECUPERACIÓN:

1. **PARA BÚSQUEDA SIMPLE** (intent="busqueda"):
   - Considera optimizar la query si es vaga o corta
   - Recupera 3-5 documentos
   - Usa score_threshold=0.0 para queries específicas

2. **PARA RESUMEN** (intent="resumen"):
   - Optimiza la query para ampliar términos
   - Recupera 8-10 documentos para cobertura amplia
   - Usa score_threshold=0.0 para incluir diversidad

3. **PARA COMPARACIÓN** (intent="comparacion"):
   - Identifica los 2+ conceptos a comparar
   - Haz búsquedas separadas para cada concepto si es necesario
   - Recupera 4-6 documentos en total
   - Asegura balance entre conceptos

4. **DECISIÓN DE OPTIMIZACIÓN**:
   - Optimiza SI: query es corta (<5 palabras), vaga, o ambigua
   - NO optimices SI: query ya es específica y clara

EJEMPLOS:

Ejemplo 1 - Búsqueda simple:
Query: "¿Qué es la diabetes?"
Razonamiento: "Query clara y específica. Busco directamente sin optimizar."
Acciones:
1. search_documents("¿Qué es la diabetes?", k=4, score_threshold=0.0)
2. log_agent_action(...)

Ejemplo 2 - Búsqueda vaga:
Query: "covid"
Razonamiento: "Query muy corta. Optimizo primero para mejores resultados."
Acciones:
1. optimize_search_query("covid", "busqueda")
2. search_documents(query_optimizada, k=4, score_threshold=0.0)
3. log_agent_action(...)

Ejemplo 3 - Comparación:
Query: "Diferencias entre diabetes tipo 1 y tipo 2"
Razonamiento: "Comparación de dos conceptos. Busco ambos en una query."
Acciones:
1. optimize_search_query(query, "comparacion")
2. search_documents(query_optimizada, k=6, score_threshold=0.0)
3. log_agent_action(...)

Ejemplo 4 - Resumen:
Query: "Resume información sobre tratamientos del cáncer"
Intent: "resumen"
Razonamiento: "Resumen requiere cobertura amplia. Recupero más documentos."
Acciones:
1. optimize_search_query(query, "resumen")
2. search_documents(query_optimizada, k=10, score_threshold=0.0)
3. log_agent_action(...)

FORMATO DE RESPUESTA FINAL:
Después de recuperar documentos, responde:
"He recuperado [N] documentos relevantes para la consulta."

Los documentos recuperados estarán disponibles automáticamente.

IMPORTANTE:
- Sé eficiente: no hagas más búsquedas de las necesarias
- Adapta k (cantidad) según el tipo de intención
- Registra tus acciones con log_agent_action
- Explica tu razonamiento"""),
            ("placeholder", "{agent_scratchpad}"),
            ("human", "Query: {query}\nIntención: {intent}\n\nRecupera los documentos más relevantes.")
        ])
    
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
            
            # Preparar input para el agente
            agent_input = {
                "query": query,
                "intent": intent
            }
            
            # Si se especifica k, agregarlo al contexto
            if k is not None:
                agent_input["input"] = f"Query: {query}\nIntención: {intent}\nRecupera exactamente {k} documentos."
            else:
                agent_input["input"] = f"Query: {query}\nIntención: {intent}\nRecupera los documentos más relevantes."
            
            # Ejecutar agente
            result = self.agent_executor.invoke(agent_input)
            
            # Extraer documentos de los pasos intermedios
            documents = []
            steps = result.get("intermediate_steps", [])
            
            for step in steps:
                if hasattr(step[0], 'tool') and 'search_documents' in step[0].tool:
                    # Extraer documentos del resultado de la búsqueda
                    search_result = step[1]
                    if isinstance(search_result, list):
                        documents.extend(search_result)
            
            logger.info(f"[AutonomousRetriever] Recuperados {len(documents)} documentos")
            
            return {
                "documents": documents,
                "query_used": query,  # Podría ser optimizada
                "count": len(documents),
                "intermediate_steps": [
                    {
                        "tool": step[0].tool if hasattr(step[0], 'tool') else "reasoning",
                        "input": str(step[0].tool_input if hasattr(step[0], 'tool_input') else "")[:100],
                        "output_preview": str(step[1])[:150]
                    }
                    for step in steps
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
