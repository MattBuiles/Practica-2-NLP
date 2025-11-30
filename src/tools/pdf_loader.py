"""
Tool para cargar documentos PDF.
PENDIENTE DE IMPLEMENTACIÓN: Persona 2/3
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class PDFLoaderTool:
    """
    Herramienta para cargar documentos PDF.
    
    TODO (Persona 2/3): Implementar carga de PDFs
    """
    
    name = "pdf_loader"
    description = "Carga y extrae texto de archivos PDF"
    
    @staticmethod
    def load_pdf(file_path: str) -> List[Dict[str, Any]]:
        """Carga un PDF. TODO: Implementar"""
        logger.warning("PDFLoaderTool - PENDIENTE DE IMPLEMENTACIÓN")
        return []
    
    @staticmethod
    def load_multiple_pdfs(file_paths: List[str]) -> List[Dict[str, Any]]:
        """Carga múltiples PDFs. TODO: Implementar"""
        return []
