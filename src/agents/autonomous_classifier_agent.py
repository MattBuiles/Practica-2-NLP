
"""Agente Clasificador Autónomo.
Clasifica intenciones directamente con el LLM sin usar herramientas.
"""
import logging
import time
import json
import re
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.config.llm_config import llm_config

logger = logging.getLogger(__name__)

# Delay entre llamadas API para evitar rate limiting
API_DELAY = 1.5


class IntentClassification(BaseModel):
    """Modelo de salida estructurada para clasificación de intención."""
    intent: str = Field(description="Intención clasificada: busqueda, resumen, comparacion, general")
    confidence: float = Field(description="Nivel de confianza (0.0 a 1.0)")
    requires_rag: bool = Field(description="Si requiere búsqueda en vector store")
    reasoning: str = Field(description="Justificación de la clasificación")


class AutonomousClassifierAgent:
    """
    Agente Clasificador Autónomo.
    
    Clasifica intenciones directamente usando el LLM sin herramientas intermedias.
    Esto es más eficiente y evita problemas de parsing con tools.
    
    CAPACIDADES:
    - Clasificación de intención (busqueda, resumen, comparacion, general)
    - Determinación de necesidad de RAG
    - Análisis contextual profundo
    """
    
    def __init__(self):
        """
        Inicializa el agente clasificador.
        
        Configura:
        - LLM para clasificación (Groq)
        - Prompt con instrucciones detalladas
        """
        logger.info("Inicializando AutonomousClassifierAgent...")
        
        # LLM para clasificación
        self.llm = llm_config.get_classifier_llm()
        
        # Prompt del sistema
        self.system_prompt = self._create_system_prompt()
        
        logger.info("AutonomousClassifierAgent inicializado (clasificación directa sin tools)")
    
    def _create_system_prompt(self) -> str:
        """
        Crea el prompt del sistema para clasificación directa.
        """
        return """Eres un clasificador de intenciones experto.

RESPONDE ÚNICAMENTE CON JSON VÁLIDO (sin markdown, sin explicaciones adicionales):

{"intent": "busqueda", "confidence": 0.9, "requires_rag": true, "reasoning": "Breve explicación"}

CATEGORÍAS DE INTENCIÓN:

1. "busqueda": Usuario busca información específica
   - Preguntas con: qué, cómo, cuándo, dónde, por qué, cuál
   - Ejemplos: "¿Qué comían los dinosaurios?", "¿Cómo se extinguieron?"
   - requires_rag: true

2. "resumen": Usuario quiere un resumen
   - Palabras clave: resume, resumen, sintetiza, principales puntos
   - Ejemplos: "Resume la información sobre T-Rex"
   - requires_rag: true

3. "comparacion": Usuario quiere comparar conceptos
   - Palabras clave: diferencia, comparar, vs, versus, entre
   - Ejemplos: "Diferencias entre carnívoros y herbívoros"
   - requires_rag: true

4. "general": Conversación general sin necesidad de documentos
   - Saludos, charla casual, preguntas sobre ti
   - Ejemplos: "Hola", "¿Cómo estás?", "Gracias"
   - requires_rag: false

VALORES:
- intent: "busqueda" | "resumen" | "comparacion" | "general"
- confidence: número entre 0.0 y 1.0
- requires_rag: true | false (booleano)
- reasoning: string breve explicando la decisión

RECUERDA: Solo JSON, sin texto adicional."""

    def classify(self, query: str) -> Dict[str, Any]:
        """
        Clasifica la intención de una consulta directamente con el LLM.
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Diccionario con clasificación:
            {
                "intent": str,
                "confidence": float,
                "requires_rag": bool,
                "reasoning": str
            }
        """
        try:
            logger.info(f"[AutonomousClassifier] Procesando: '{query[:100]}'")
            
            # Delay para evitar rate limiting
            time.sleep(API_DELAY)
            
            # Crear prompt para clasificación
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                ("user", "Clasifica esta consulta: {query}")
            ])
            
            # Invocar LLM directamente
            messages = prompt.format_messages(query=query)
            response = self.llm.invoke(messages)
            
            # Parsear respuesta JSON
            classification = self._parse_classification_response(response.content)
            
            logger.info(f"[AutonomousClassifier] Clasificado como: {classification['intent']} (confianza: {classification['confidence']:.2f})")
            
            return classification
            
        except Exception as e:
            logger.error(f"[AutonomousClassifier] Error: {str(e)}")
            # Fallback con heurísticas simples
            return self._fallback_classification(query, str(e))
    
    def _parse_classification_response(self, content: str) -> Dict[str, Any]:
        """
        Parsea la respuesta JSON del LLM con múltiples estrategias de fallback.
        """
        text = content.strip()
        
        # 1. Limpiar markdown
        text = text.replace('```json', '').replace('```', '').strip()
        
        # 2. Intentar encontrar y limpiar el JSON
        # Buscar desde { hasta }
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = text[start_idx:end_idx + 1]
            
            # Normalizar el JSON: reemplazar newlines y espacios múltiples
            json_str = ' '.join(json_str.split())
            
            try:
                data = json.loads(json_str)
                
                # Extraer y validar campos
                intent = str(data.get('intent', 'busqueda')).lower().strip()
                if intent not in ['busqueda', 'resumen', 'comparacion', 'general']:
                    intent = 'busqueda'
                
                confidence = data.get('confidence', 0.8)
                if isinstance(confidence, str):
                    try:
                        confidence = float(confidence)
                    except:
                        confidence = 0.8
                confidence = max(0.0, min(1.0, float(confidence)))
                
                requires_rag = data.get('requires_rag', True)
                if isinstance(requires_rag, str):
                    requires_rag = requires_rag.lower() in ['true', '1', 'yes', 'si']
                
                reasoning = str(data.get('reasoning', 'Clasificación automática'))
                
                return {
                    "intent": intent,
                    "confidence": confidence,
                    "requires_rag": bool(requires_rag),
                    "reasoning": reasoning
                }
            except json.JSONDecodeError as e:
                logger.debug(f"JSON decode error: {e}, intentando inferir del texto")
        
        # 3. Si JSON falla, inferir del contenido
        return self._infer_from_text(content)
    
    def _infer_from_text(self, text: str) -> Dict[str, Any]:
        """
        Infiere la clasificación del texto cuando el JSON falla.
        """
        text_lower = text.lower()
        
        intent = "busqueda"
        if '"resumen"' in text_lower or "resumen" in text_lower:
            intent = "resumen"
        elif '"comparacion"' in text_lower or "comparacion" in text_lower or "comparar" in text_lower:
            intent = "comparacion"
        elif '"general"' in text_lower:
            intent = "general"
        
        return {
            "intent": intent,
            "confidence": 0.7,
            "requires_rag": intent != "general",
            "reasoning": "Inferido del contenido de la respuesta"
        }
    
    def _fallback_classification(self, query: str, error: str) -> Dict[str, Any]:
        """
        Clasificación de respaldo usando heurísticas simples.
        """
        query_lower = query.lower()
        
        # Detectar comparación
        if any(word in query_lower for word in ['diferencia', 'comparar', 'comparacion', 'vs', 'versus', 'entre']):
            intent = "comparacion"
        # Detectar resumen
        elif any(word in query_lower for word in ['resume', 'resumen', 'sintetiza', 'principales']):
            intent = "resumen"
        # Detectar general
        elif any(word in query_lower for word in ['hola', 'gracias', 'adios', 'como estas']):
            intent = "general"
        # Default: búsqueda
        else:
            intent = "busqueda"
        
        return {
            "intent": intent,
            "confidence": 0.6,
            "requires_rag": intent != "general",
            "reasoning": f"Clasificación por heurísticas (error original: {error[:100]})"
        }
