"""
Utilidades de formateo para respuestas y logs.
"""
from typing import List, Dict, Any
from datetime import datetime


def format_response_with_citations(response: str, sources: List[Dict[str, Any]]) -> str:
    """
    Formatea una respuesta incluyendo las citas de los documentos fuente.
    
    Args:
        response: La respuesta generada
        sources: Lista de documentos fuente con metadata
    
    Returns:
        Respuesta formateada con citas
    """
    formatted = response + "\n\n---\n**Fuentes consultadas:**\n"
    
    for i, source in enumerate(sources, 1):
        title = source.get('title', 'Documento sin título')
        doc_id = source.get('id', 'unknown')
        
        formatted += f"[{i}] {title} (ID: {doc_id})\n"
    
    return formatted


def format_comparison_response(doc1_summary: str, doc2_summary: str, 
                               differences: List[str], similarities: List[str]) -> str:
    """
    Formatea una respuesta de comparación entre documentos.
    """
    response = "### Comparación de Documentos\n\n"
    
    response += "**Documento 1:**\n"
    response += doc1_summary + "\n\n"
    
    response += "**Documento 2:**\n"
    response += doc2_summary + "\n\n"
    
    if similarities:
        response += "**Similitudes:**\n"
        for sim in similarities:
            response += f"- {sim}\n"
        response += "\n"
    
    if differences:
        response += "**Diferencias:**\n"
        for diff in differences:
            response += f"- {diff}\n"
    
    return response


def format_summary_response(key_points: List[str], summary: str) -> str:
    """
    Formatea una respuesta de resumen con puntos clave.
    """
    response = "### Resumen\n\n"
    response += summary + "\n\n"
    
    if key_points:
        response += "**Puntos clave:**\n"
        for point in key_points:
            response += f"- {point}\n"
    
    return response


def format_trace_summary(trace_data: Dict[str, Any]) -> str:
    """
    Formatea un resumen de la traza de ejecución para mostrar al usuario.
    """
    summary = f"""
### Información de Ejecución

**Consulta:** {trace_data.get('query', 'N/A')}
**Tiempo de ejecución:** {trace_data.get('metadata', {}).get('execution_time_seconds', 0):.2f}s
**Agentes involucrados:** {', '.join(trace_data.get('metadata', {}).get('agents_involved', []))}
**Documentos recuperados:** {len(trace_data.get('metadata', {}).get('documents_retrieved', []))}
**Llamadas a LLM:** {trace_data.get('metadata', {}).get('total_llm_calls', 0)}
"""
    return summary.strip()


def format_error_message(error_type: str, details: str) -> str:
    """
    Formatea un mensaje de error user-friendly.
    """
    error_messages = {
        "no_documents": "No se encontraron documentos relevantes para tu consulta. Intenta reformular la pregunta.",
        "validation_failed": "La respuesta generada no cumplió con los criterios de calidad. Intentando nuevamente...",
        "max_retries": "Se alcanzó el número máximo de intentos. La mejor respuesta generada se muestra a continuación.",
        "llm_error": "Error al comunicarse con el modelo de lenguaje. Por favor, intenta nuevamente.",
        "indexing_error": "Error al acceder al índice de documentos. Verifica que los documentos estén indexados.",
    }
    
    base_message = error_messages.get(error_type, "Ha ocurrido un error inesperado.")
    
    return f"⚠️ {base_message}\n\nDetalles técnicos: {details}"


def timestamp() -> str:
    """Genera un timestamp formateado."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
