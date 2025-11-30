"""
Agente Clasificador de Intención.
Utiliza Gemini para análisis contextual profundo de la consulta del usuario.
"""
import logging
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.config.llm_config import llm_config

logger = logging.getLogger(__name__)


class IntentClassification(BaseModel):
    """Modelo para la clasificación de intención."""
    intent: str = Field(description="Intención clasificada: busqueda, resumen, comparacion, general")
    confidence: float = Field(description="Nivel de confianza (0.0 a 1.0)")
    requires_rag: bool = Field(description="Si requiere búsqueda en vector store")
    reasoning: str = Field(description="Justificación de la clasificación")


class ClassifierAgent:
    """
    Agente Clasificador de Intención.
    
    Responsable de:
    - Clasificar la intención del usuario en 4 categorías
    - Determinar si se requiere acceso al vector store
    - Proporcionar razonamiento para la decisión
    """
    
    VALID_INTENTS = ["busqueda", "resumen", "comparacion", "general"]
    
    def __init__(self):
        """Inicializa el agente clasificador con Gemini."""
        self.llm = llm_config.get_classifier_llm()
        
        # Configurar LLM con salida estructurada
        self.structured_llm = self.llm.with_structured_output(IntentClassification)
        
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("user", "{query}")
        ])
        
        logger.info("ClassifierAgent inicializado con Gemini")
    
    def _get_system_prompt(self) -> str:
        """Genera el prompt del sistema para clasificación."""
        return """Eres un agente experto en clasificación de intenciones para un sistema RAG.

Tu tarea es clasificar la consulta del usuario en UNA de estas 4 categorías:

1. **busqueda**: El usuario busca información específica, hechos o datos del corpus de documentos.
   - Ejemplos: "¿Qué es la diabetes?", "Dame información sobre tratamientos del cáncer"
   - Requires RAG: SÍ

2. **resumen**: El usuario solicita un resumen de uno o varios documentos.
   - Ejemplos: "Resume el artículo sobre hipertensión", "Hazme un resumen de los documentos"
   - Requires RAG: SÍ

3. **comparacion**: El usuario quiere comparar dos o más documentos o conceptos.
   - Ejemplos: "Compara el tratamiento A con el B", "Diferencias entre diabetes tipo 1 y 2"
   - Requires RAG: SÍ

4. **general**: Consulta general que NO requiere buscar en los documentos.
   - Ejemplos: "¿Cómo estás?", "Cuéntame un chiste", "¿Qué hora es?"
   - Requires RAG: NO

IMPORTANTE:
- Analiza cuidadosamente el contexto y la intención real del usuario
- Si hay duda entre categorías, elige la más específica
- Proporciona un razonamiento claro de tu decisión
- Asigna un nivel de confianza honesto (0.0 a 1.0)

Responde SOLO con los campos del modelo IntentClassification (intent, confidence, requires_rag, reasoning).
"""
    
    def classify(self, query: str) -> Dict[str, Any]:
        """
        Clasifica la intención de una consulta.
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Diccionario con intención, confianza, requires_rag y razonamiento
        """
        try:
            logger.info(f"Clasificando consulta: {query[:100]}...")
            
            # Preparar prompt
            messages = self.prompt_template.format_messages(query=query)
            
            # Invocar LLM con salida estructurada
            classification = self.structured_llm.invoke(messages)
            
            # Validar intención
            if classification.intent not in self.VALID_INTENTS:
                logger.warning(f"Intención inválida: {classification.intent}, usando 'general'")
                classification.intent = "general"
                classification.requires_rag = False
            
            result = {
                "intent": classification.intent,
                "confidence": classification.confidence,
                "requires_rag": classification.requires_rag,
                "reasoning": classification.reasoning
            }
            
            logger.info(f"Clasificación: {classification.intent} (confianza: {classification.confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error en clasificación: {str(e)}")
            # Fallback a clasificación general
            return {
                "intent": "general",
                "confidence": 0.5,
                "requires_rag": False,
                "reasoning": f"Error en clasificación: {str(e)}"
            }
    
    def classify_batch(self, queries: list[str]) -> list[Dict[str, Any]]:
        """
        Clasifica múltiples consultas.
        
        Args:
            queries: Lista de consultas
            
        Returns:
            Lista de clasificaciones
        """
        results = []
        for query in queries:
            result = self.classify(query)
            results.append(result)
        
        return results
