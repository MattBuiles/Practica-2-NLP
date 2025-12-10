"""
Tool para optimizar queries de búsqueda usando LLM.
Mejora las consultas del usuario para maximizar la recuperación de documentos relevantes.
"""
import logging
from typing import Dict, Any
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate

from src.config.llm_config import llm_config

logger = logging.getLogger(__name__)


@tool
def optimize_search_query(query: str, intent: str = "busqueda") -> str:
    """
    Optimiza una consulta de búsqueda para mejorar la recuperación de documentos.
    
    Esta herramienta debe usarse cuando:
    - La consulta del usuario es vaga o ambigua
    - Se necesita expandir la consulta con sinónimos y términos relacionados
    - Se quiere mejorar la calidad de los resultados de búsqueda
    - La consulta es muy corta o demasiado larga
    
    Args:
        query: La consulta original del usuario
               Ejemplo: "qué dice sobre covid"
        intent: El tipo de intención (busqueda, resumen, comparacion, general)
                Ayuda a adaptar la optimización al contexto
    
    Returns:
        Consulta optimizada expandida con términos relevantes.
        Ejemplo: "información efectos síntomas tratamiento covid-19 coronavirus"
        
    Ejemplo de uso:
        # Expandir consulta simple
        optimized = optimize_search_query("diabetes", "busqueda")
        # Resultado: "diabetes mellitus tipo 1 tipo 2 síntomas tratamiento glucosa"
        
        # Optimizar para comparación
        optimized = optimize_search_query("covid vs gripe", "comparacion")
        # Resultado: "comparación diferencias covid-19 influenza gripe síntomas"
    """
    try:
        logger.info(f"Optimizando query: '{query}' (intent: {intent})")
        
        # Configurar LLM rápido para optimización
        llm = llm_config.get_retriever_llm()
        
        # Prompt de optimización
        prompt = ChtPromptTemplate.from_messages([
            ("system", """Eres un experto en optimización de consultas para búsqueda semántica.

Tu tarea es reformular la consulta del usuario para mejorar la recuperación de documentos relevantes.

ESTRATEGIAS:
1. Expandir con sinónimos y términos relacionados
2. Eliminar palabras vacías no informativas ("qué", "dice", "sobre", etc.)
3. Mantener la intención original
4. Añadir contexto relevante del dominioa

SEGÚN INTENCIÓN:
- busqueda: Términos específicos y precisos
- resumen: Términos más generales y amplios
- comparacion: Incluir ambos conceptos explícitamente
- general: Mantener simple

EJEMPLOS:
Query: "qué es diabetes"
Optimizada: "diabetes mellitus definición síntomas causas tratamiento"

Query: "covid vs gripe"
Optimizada: "comparación diferencias covid-19 influenza gripe síntomas transmisión"

Query: "resume artículo"
Optimizada: "resumen puntos clave información principal contenido"

Responde SOLO con la consulta optimizada, sin explicaciones."""),
            ("user", "Query: {query}\nIntención: {intent}")
        ])
        
        messages = prompt.format_messages(query=query, intent=intent)
        response = llm.invoke(messages)
        
        optimized = response.content.strip()
        logger.info(f"Query optimizada: '{optimized}'")
        
        return optimized
        
    except Exception as e:
        logger.error(f"Error optimizando query: {str(e)}")
        # En caso de error, devolver query original
        return query
