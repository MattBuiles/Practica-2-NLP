"""
Gestión de embeddings.
PENDIENTE DE IMPLEMENTACIÓN: Persona 2/3
"""
import logging

logger = logging.getLogger(__name__)


class EmbeddingsManager:
    """
    Gestor de embeddings.
    
    TODO (Persona 2/3): Implementar gestión de embeddings
    - Configurar modelo de embeddings
    - Generar embeddings para textos
    """
    
    def __init__(self):
        """Inicializa el gestor de embeddings."""
        logger.warning("EmbeddingsManager - PENDIENTE DE IMPLEMENTACIÓN (Persona 2/3)")
        self.embeddings = None
    
    def get_embedding_dimension(self) -> int:
        """Retorna dimensión de embeddings. TODO: Implementar"""
        return 384  # Placeholder


# Instancia global
embeddings_manager = EmbeddingsManager()
