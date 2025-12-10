"""
Tool para clasificar intención de consultas.
Determina si el usuario busca información, resumen, comparación o conversación general.
"""
import logging
import json
import re
import time
from typing import Dict, Any
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.config.llm_config import llm_config

logger = logging.getLogger(__name__)

# Delay entre llamadas API
API_DELAY = 1.0


def _parse_classification_json(text: str) -> Dict[str, Any]:
    """Parsea respuesta JSON de clasificación, corrigiendo tipos."""
    # Limpiar markdown y espacios
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()
    
    # PRIMERO: Intentar extraer campos con regex (más robusto ante newlines)
    intent_match = re.search(r'"intent"\s*:\s*"(\w+)"', text)
    conf_match = re.search(r'"confidence"\s*:\s*([\d.]+)', text)
    rag_match = re.search(r'"requires_rag"\s*:\s*(true|false)', text, re.I)
    reasoning_match = re.search(r'"reasoning"\s*:\s*"([^"]+)"', text)
    
    # Si encontramos el intent, construir respuesta directamente
    if intent_match:
        return {
            "intent": intent_match.group(1),
            "confidence": float(conf_match.group(1)) if conf_match else 0.85,
            "requires_rag": rag_match.group(1).lower() == 'true' if rag_match else True,
            "reasoning": reasoning_match.group(1) if reasoning_match else "Extraído con regex"
        }
    
    # Si no encontramos con regex, intentar JSON limpio
    cleaned = re.sub(r'\n\s*', ' ', text)
    json_match = re.search(r'\{[^{}]+\}', cleaned)
    if json_match:
        try:
            data = json.loads(json_match.group())
            # Corregir tipos
            if 'confidence' in data and isinstance(data['confidence'], str):
                data['confidence'] = float(data['confidence'])
            if 'requires_rag' in data and isinstance(data['requires_rag'], str):
                data['requires_rag'] = data['requires_rag'].lower() == 'true'
            return data
        except json.JSONDecodeError:
            pass
    
    # Fallback final: analizar texto para inferir intent
    text_lower = text.lower()
    if "compar" in text_lower:
        intent = "comparacion"
    elif "resum" in text_lower:
        intent = "resumen"
    elif "general" in text_lower or "hola" in text_lower or "salud" in text_lower:
        intent = "general"
    else:
        intent = "busqueda"
    return {
        "intent": intent,
        "confidence": 0.7,
        "requires_rag": intent != "general",
        "reasoning": f"Inferido del texto"
    }
    
    # Si llegamos aquí, data fue parseado correctamente
    # Corregir tipos si es necesario
    if 'confidence' in data and isinstance(data['confidence'], str):
        data['confidence'] = float(data['confidence'])
    if 'requires_rag' in data and isinstance(data['requires_rag'], str):
        data['requires_rag'] = data['requires_rag'].lower() == 'true'
        
    return data


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
        
        # Delay para evitar rate limiting
        time.sleep(API_DELAY)
        
        # Configurar LLM para clasificación (SIN structured_output)
        llm = llm_config.get_classifier_llm()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un experto en clasificación de intenciones para sistemas RAG.

RESPONDE ÚNICAMENTE CON JSON VÁLIDO (sin markdown):

{
  "intent": "busqueda",
  "confidence": 0.9,
  "requires_rag": true,
  "reasoning": "El usuario busca información específica"
}

CATEGORÍAS (intent):
1. "busqueda": Busca información específica (qué, cómo, cuándo) → requires_rag=true
2. "resumen": Solicita resumen de documentos → requires_rag=true  
3. "comparacion": Quiere comparar conceptos (vs, diferencia) → requires_rag=true
4. "general": Conversación general (saludos, charla) → requires_rag=false

VALORES:
- intent: string ("busqueda", "resumen", "comparacion", "general")
- confidence: número 0.0 a 1.0
- requires_rag: booleano (true/false)
- reasoning: string breve

SOLO RESPONDE CON JSON."""),
            ("user", "{query}")
        ])
        
        messages = prompt.format_messages(query=query)
        response = llm.invoke(messages)
        classification = _parse_classification_json(response.content)
        
        result = {
            "intent": classification.get("intent", "busqueda"),
            "confidence": float(classification.get("confidence", 0.7)),
            "requires_rag": bool(classification.get("requires_rag", True)),
            "reasoning": classification.get("reasoning", "Sin razonamiento")
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
