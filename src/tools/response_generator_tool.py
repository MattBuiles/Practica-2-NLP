"""
Tool para generar respuestas usando RAG.
Combina documentos recuperados con la consulta del usuario para generar respuestas contextuales.
"""
import logging
from typing import List, Dict, Any
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate

from src.config.llm_config import llm_config

logger = logging.getLogger(__name__)


@tool
def generate_rag_response(query: str, documents: List[Dict[str, Any]], intent: str = "busqueda") -> str:
    """
    Genera una respuesta basada en documentos recuperados (RAG).
    
    Esta herramienta debe usarse cuando:
    - Se tienen documentos relevantes y se necesita generar una respuesta
    - Se quiere responder una pregunta usando información específica
    - Se necesita sintetizar información de múltiples fuentes
    - Se requiere una respuesta con citas a las fuentes
    
    Args:
        query: La pregunta o solicitud del usuario
               Ejemplo: "¿Cuáles son los síntomas del COVID-19?"
        documents: Lista de documentos relevantes con content y metadata
                   Formato: [{"content": "...", "metadata": {"source": "..."}}]
        intent: Tipo de respuesta (busqueda, resumen, comparacion)
                Adapta el estilo de la respuesta al contexto
    
    Returns:
        Respuesta generada con citas a las fuentes.
        Incluye referencias como [Fuente 1], [Fuente 2], etc.
        
    Ejemplo de uso:
        docs = search_documents("síntomas COVID-19", k=3)
        response = generate_rag_response(
            "¿Cuáles son los síntomas?", 
            docs, 
            intent="busqueda"
        )
    """
    try:
        logger.info(f"Generando respuesta RAG para: '{query}' (intent: {intent}, docs: {len(documents)})")
        
        if not documents:
            return "No se encontraron documentos relevantes para responder la consulta."
        
        # Preparar contexto de documentos
        context_parts = []
        for idx, doc in enumerate(documents, 1):
            source = doc.get('metadata', {}).get('source', 'Desconocido')
            content = doc.get('content', '')
            context_parts.append(f"[Fuente {idx}: {source}]\n{content}")
        
        context = "\n\n".join(context_parts)
        
        # Seleccionar prompt según intención
        if intent == "resumen":
            system_prompt = """Eres un asistente experto en sintetizar información.

TAREA: Crear un resumen estructurado de los documentos proporcionados.

INSTRUCCIONES:
1. Identifica los puntos clave de cada fuente
2. Organiza la información de forma lógica (usa viñetas o numeración)
3. Sintetiza sin perder información importante
4. Cita las fuentes de cada punto [Fuente X]
5. Mantén un estilo claro y profesional

NO inventes información no presente en las fuentes."""
        
        elif intent == "comparacion":
            system_prompt = """Eres un asistente experto en análisis comparativo.

TAREA: Comparar conceptos o documentos de forma estructurada.

INSTRUCCIONES:
1. Identifica los elementos a comparar
2. Organiza la comparación punto por punto
3. Destaca similitudes y diferencias claramente
4. Usa una estructura (tabla, lista, o secciones)
5. Cita las fuentes de cada afirmación [Fuente X]
6. Sé objetivo y basado en evidencia

NO hagas juicios sin respaldo en las fuentes."""
        
        else:  # busqueda
            system_prompt = """Eres un asistente experto en proporcionar información precisa.

TAREA: Responder la pregunta usando ÚNICAMENTE la información proporcionada.

INSTRUCCIONES:
1. Responde de forma directa y concisa
2. Usa SOLO información del contexto
3. SIEMPRE cita las fuentes [Fuente X]
4. Si la información no está disponible, indícalo claramente
5. Organiza la respuesta de forma clara
6. Cada afirmación debe tener su cita

NO inventes ni asumas información no presente."""
        
        # Configurar LLM para generación
        llm = llm_config.get_rag_llm()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", """Contexto de documentos:
{context}

Pregunta del usuario: {query}

Responde de forma precisa y fundamentada:""")
        ])
        
        messages = prompt.format_messages(context=context, query=query)
        response = llm.invoke(messages)
        
        answer = response.content.strip()
        logger.info(f"Respuesta generada ({len(answer)} caracteres)")
        
        return answer
        
    except Exception as e:
        logger.error(f"Error generando respuesta RAG: {str(e)}")
        return f"Error al generar respuesta: {str(e)}"


@tool
def generate_general_response(query: str) -> str:
    """
    Genera una respuesta general sin usar documentos (sin RAG).
    
    Esta herramienta debe usarse cuando:
    - La consulta es conversacional (saludos, charla general)
    - No se requiere información específica de documentos
    - Es una pregunta de conocimiento general
    - El usuario no está buscando información del corpus
    
    Args:
        query: La consulta del usuario
               Ejemplo: "¿Cómo estás?", "Cuéntame un chiste"
    
    Returns:
        Respuesta directa del LLM sin contexto de documentos.
        
    Ejemplo de uso:
        response = generate_general_response("¿Qué hora es?")
        response = generate_general_response("Hola, ¿cómo estás?")
    """
    try:
        logger.info(f"Generando respuesta general para: '{query}'")
        
        # Usar LLM apropiado para conversación
        llm = llm_config.get_general_llm()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un asistente amigable y útil.

Responde de forma natural y conversacional.
Sé conciso pero amable.
Si te preguntan sobre capacidades, explica que puedes:
- Buscar información en documentos especializados
- Resumir y comparar documentos
- Responder preguntas generales"""),
            ("user", "{query}")
        ])
        
        messages = prompt.format_messages(query=query)
        response = llm.invoke(messages)
        
        answer = response.content.strip()
        logger.info(f"Respuesta general generada")
        
        return answer
        
    except Exception as e:
        logger.error(f"Error generando respuesta general: {str(e)}")
        return "Disculpa, hubo un error al procesar tu consulta."
