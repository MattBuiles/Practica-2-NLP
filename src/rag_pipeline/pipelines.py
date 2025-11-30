"""
Pipeline RAG completo.
PENDIENTE DE IMPLEMENTACIÓN: Persona 2/3
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Pipeline RAG completo.
    
    TODO (Persona 2/3): Implementar pipeline
    - Indexación de documentos
    - Búsqueda
    - Integración componentes
    """
    
    def __init__(self):
        """Inicializa el pipeline."""
        logger.warning("RAGPipeline - PENDIENTE DE IMPLEMENTACIÓN (Persona 2/3)")
    
    def index_directory(self, directory_path: str) -> Dict[str, Any]:
        """Indexa directorio. TODO: Implementar"""
        logger.warning("RAGPipeline.index_directory() - PENDIENTE DE IMPLEMENTACIÓN")
        return {"status": "pending", "documents_indexed": 0}
    
    def query(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Consulta. TODO: Implementar"""
        logger.warning("RAGPipeline.query() - PENDIENTE DE IMPLEMENTACIÓN")
        return []
