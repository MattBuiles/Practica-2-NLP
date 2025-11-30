"""
Agente de Generación de Respuestas RAG.
PENDIENTE DE IMPLEMENTACIÓN: Persona 2/3
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class RAGAgent:
    """
    Agente de Generación de Respuestas RAG.
    
    TODO (Persona 2/3): Implementar funcionalidad completa
    - Generar respuestas basadas en contexto recuperado
    - Incluir citas de fuentes
    - Adaptar respuesta según intención (búsqueda, resumen, comparación)
    """
    
    def __init__(self):
        """Inicializa el agente RAG."""
        # TODO: Implementar inicialización con LLM
        logger.warning("RAGAgent - PENDIENTE DE IMPLEMENTACIÓN (Persona 2/3)")
    
    def generate_response(self, query: str, documents: List[Dict[str, Any]], 
                         intent: str = "busqueda") -> Dict[str, Any]:
        """
        Genera una respuesta basada en documentos recuperados.
        TODO (Persona 2/3): Implementar lógica completa
        """
        logger.warning("RAGAgent.generate_response() - PENDIENTE DE IMPLEMENTACIÓN")
        return {
            "response": "[PENDIENTE: Implementar generación RAG]",
            "sources": [],
            "intent": intent
        }
    
    def generate_general_response(self, query: str) -> str:
        """
        Genera una respuesta general sin contexto RAG.
        TODO (Persona 2/3): Implementar
        """
        logger.warning("RAGAgent.generate_general_response() - PENDIENTE DE IMPLEMENTACIÓN")
        return "[PENDIENTE: Implementar respuesta general]"
    
    def format_response_with_sources(self, response_data: Dict[str, Any]) -> str:
        """
        Formatea la respuesta con las fuentes citadas.
        TODO (Persona 2/3): Implementar
        """
        return response_data.get('response', '')
