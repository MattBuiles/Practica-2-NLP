"""
Tool para clasificar intención de consultas.
Determina si el usuario busca información, resumen, comparación o conversación general.
"""
import logging
from typing import Dict, Any
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.config.llm_config import llm_config

logger = logging.getLogger(__name__)


class IntentClassification(BaseModel):
    """Clasificación de intención del usuario."""
    intent: str = Field(description="Intención: busqueda, resumen, comparacion, general")
    confidence: float = Field(description="Confianza 0-1")
    requires_rag: bool = Field(description="Si requiere búsqueda en documentos")
    reasoning: str = Field(description="Justificación de la clasificación")


@tool
def classify_intent(query: str) -> Dict[str, Any]:
    """
    Clasifica la intención del usuario en una consulta.
    
    Esta herramienta debe usarse cuando:
    - Se recibe una nueva consulta del usuario
    - Se necesita determinar qué tipo de procesamiento requiere
    - Se quiere decidir si usar RAG o respuesta directa
    - Es el primer paso en el procesamiento de una consulta
    
    CATEGORÍAS DE INTENCIÓN:
    
    1. **busqueda**: El usuario busca información específica de documentos
       - Ejemplos: "¿Qué es la diabetes?", "Explícame el COVID-19"
       - Acción: Buscar en vector store y generar respuesta RAG
    
    2. **resumen**: El usuario quiere un resumen de documentos
       - Ejemplos: "Resume el artículo X", "Hazme un resumen"
       - Acción: Recuperar múltiples documentos y sintetizar
    
    3. **comparacion**: El usuario quiere comparar conceptos/documentos
       - Ejemplos: "Diferencias entre A y B", "Compara X con Y"
       - Acción: Buscar ambos conceptos y hacer análisis comparativo
    
    4. **general**: Consulta conversacional sin necesidad de documentos
       - Ejemplos: "Hola", "¿Cómo estás?", "Cuéntame un chiste"
       - Acción: Respuesta directa sin RAG
    
    Args:
        query: La consulta del usuario en lenguaje natural
    
    Returns:
        Diccionario con clasificación:
        {
            "intent": str,  # busqueda, resumen, comparacion, general
            "confidence": float,  # 0.0 a 1.0
            "requires_rag": bool,  # Si necesita buscar en documentos
            "reasoning": str  # Explicación de la decisión
        }
        
    Ejemplo de uso:
        result = classify_intent("¿Qué es el COVID-19?")
        # result = {
        #     "intent": "busqueda",
        #     "confidence": 0.95,
        #     "requires_rag": True,
        #     "reasoning": "Usuario busca definición específica"
        # }
    """
    try:
        logger.info(f"Clasificando intención de: '{query}'")
        
        # Configurar LLM para clasificación (Gemini - comprensión contextual)
        llm = llm_config.get_classifier_llm()
        structured_llm = llm.with_structured_output(IntentClassification)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un experto en clasificación de intenciones para sistemas RAG.

Clasifica la consulta en UNA de estas 4 categorías:

1. **busqueda**: Busca información específica en documentos
   - Preguntas tipo qué, cómo, cuándo, dónde
   - Solicitudes de explicación o definición
   - Búsqueda de datos o hechos concretos
   - Requires RAG: SÍ

2. **resumen**: Solicita resumen de documentos
   - Palabras clave: "resume", "resumen", "sintetiza"
   - Referencias explícitas a documentos
   - Requires RAG: SÍ

3. **comparacion**: Quiere comparar conceptos o documentos
   - Palabras clave: "compara", "diferencia", "vs", "versus"
   - Menciona dos o más elementos a contrastar
   - Requires RAG: SÍ

4. **general**: Conversación general sin necesidad de documentos
   - Saludos, despedidas
   - Preguntas sobre el sistema
   - Charla casual
   - Requires RAG: NO

IMPORTANTE:
- Analiza el contexto completo, no solo palabras clave
- Si hay duda, prioriza: comparacion > resumen > busqueda > general
- Asigna confianza honesta (0.0 a 1.0)

Responde SOLO con los campos del modelo IntentClassification."""),
            ("user", "{query}")
        ])
        
        messages = prompt.format_messages(query=query)
        classification = structured_llm.invoke(messages)
        
        result = {
            "intent": classification.intent,
            "confidence": classification.confidence,
            "requires_rag": classification.requires_rag,
            "reasoning": classification.reasoning
        }
        
        logger.info(f"Intención clasificada: {result['intent']} (confianza: {result['confidence']:.2f})")
        
        return result
        
    except Exception as e:
        logger.error(f"Error en clasificación: {str(e)}")
        # Valor por defecto seguro
        return {
            "intent": "busqueda",
            "confidence": 0.5,
            "requires_rag": True,
            "reasoning": f"Error en clasificación: {str(e)}"
        }
