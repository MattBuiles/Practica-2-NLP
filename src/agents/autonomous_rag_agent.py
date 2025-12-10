"""
Agente RAG Autónomo con Tools.
Genera respuestas basadas en contexto de forma inteligente y adaptativa.
"""
import logging
import time
from typing import Dict, Any, List
from langchain.agents import create_agent
from pydantic import BaseModel, Field

from src.config.llm_config import llm_config
from src.tools import RAG_TOOLS

logger = logging.getLogger(__name__)

# Delay entre llamadas API para evitar rate limiting
API_DELAY = 1.5


class RAGResponse(BaseModel):
    """Modelo de salida estructurada para generación RAG."""
    response: str = Field(description="Respuesta generada")
    used_rag: bool = Field(description="Si se utilizó RAG (contexto documental)")
    sources_count: int = Field(description="Número de fuentes utilizadas")
    confidence: float = Field(description="Confianza en la respuesta (0.0 a 1.0)")


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
        
        NOTA: Genera directamente con LLM en vez de usar tools porque
        Groq tiene problemas pasando arrays como parámetros de tools.
        
        Args:
            query: Consulta del usuario
            documents: Documentos recuperados (puede ser vacío)
            intent: Tipo de intención (busqueda, resumen, comparacion, general)
            
        Returns:
            Diccionario con respuesta generada
        """
        try:
            logger.info(f"[AutonomousRAG] Query: '{query[:80]}', docs: {len(documents)}, intent: {intent}")
            
            # Delay para evitar rate limiting
            time.sleep(API_DELAY)
            
            # Si no hay documentos y es intent general, respuesta conversacional
            if not documents and intent == "general":
                response = self._generate_general_response(query)
                return {
                    "response": response,
                    "used_rag": False,
                    "num_documents": 0,
                    "intermediate_steps": [{"action": "general_response"}]
                }
            
            # Generar respuesta RAG directamente (sin pasar por agent/tools)
            response = self._generate_rag_response_direct(query, documents, intent)
            
            return {
                "response": response,
                "used_rag": True,
                "num_documents": len(documents),
                "intermediate_steps": [{"action": "rag_response", "docs": len(documents)}]
            }
            
        except Exception as e:
            logger.error(f"[AutonomousRAG] Error: {str(e)}")
            
            # Fallback: generar respuesta básica
            if documents and intent != "general":
                fallback = f"Encontré {len(documents)} documentos relevantes, pero hubo un error al procesar: {str(e)}"
            else:
                fallback = f"Disculpa, hubo un error: {str(e)}"
            
            return {
                "response": fallback,
                "used_rag": False,
                "num_documents": len(documents),
                "error": str(e),
                "intermediate_steps": []
            }
    
    def _generate_rag_response_direct(self, query: str, documents: List[Dict[str, Any]], intent: str) -> str:
        """Genera respuesta RAG directamente con el LLM, sin pasar por tools."""
        import os
        
        # Preparar contexto de documentos CON nombres de fuentes
        context_parts = []
        source_references = []
        
        for idx, doc in enumerate(documents[:5], 1):  # Limitar a 5 docs
            # Obtener nombre del archivo fuente
            metadata = doc.get('metadata', {})
            source_path = metadata.get('source', 'Documento desconocido')
            # Extraer solo el nombre del archivo sin ruta
            source_name = os.path.basename(source_path) if source_path else f'Documento {idx}'
            # Limpiar extensión y caracteres especiales
            source_name = source_name.replace('.html', '').replace('.txt', '').replace('.pdf', '')
            source_name = source_name.replace('_', ' ').replace('  ', ' ')[:80]
            
            content = doc.get('content', '')[:800]  # Limitar contenido
            context_parts.append(f"[Fuente {idx} - {source_name}]:\n{content}")
            source_references.append(f"[Fuente {idx}]: {source_name}")
        
        context = "\n\n".join(context_parts)
        references = "\n".join(source_references)
        
        # Seleccionar instrucciones según intent
        if intent == "resumen":
            instructions = "Crea un RESUMEN estructurado. Usa viñetas, destaca puntos clave."
        elif intent == "comparacion":
            instructions = "Haz una COMPARACIÓN punto por punto. Destaca similitudes y diferencias."
        else:
            instructions = "Responde de forma DIRECTA y PRECISA. Sé conciso."
        
        prompt = f"""Responde la siguiente pregunta usando SOLO la información del contexto.

PREGUNTA: {query}

CONTEXTO:
{context}

INSTRUCCIONES:
- {instructions}
- Cita las fuentes usando [Fuente X] cuando uses información de ellas
- NO inventes información que no esté en el contexto
- Si no hay suficiente información, indícalo claramente

RESPUESTA:"""
        
        response = self.llm.invoke(prompt)
        response_text = response.content
        
        # Agregar referencias al final
        response_text += f"\n\n---\n**Referencias:**\n{references}"
        
        return response_text
    
    def _generate_general_response(self, query: str) -> str:
        """Genera respuesta conversacional sin RAG."""
        prompt = f"""Eres un asistente amigable sobre dinosaurios y paleontología.
        
Responde de forma conversacional a: {query}

Sé breve y amigable."""
        
        response = self.llm.invoke(prompt)
        return response.content
