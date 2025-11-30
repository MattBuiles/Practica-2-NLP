"""
Agente Indexador.
Responsable de la ingestión, limpieza, chunking e indexación de documentos.
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.tools import PDFLoaderTool, HTMLLoaderTool, TextCleanerTool
from src.rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)


class IndexerAgent:
    """
    Agente de Indexación.
    
    Responsable de:
    - Cargar documentos de múltiples formatos
    - Limpiar y normalizar texto
    - Chunkear documentos
    - Indexar en FAISS con embeddings
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Inicializa el agente indexador.
        
        Args:
            chunk_size: Tamaño de chunks
            chunk_overlap: Overlap entre chunks
        """
        self.pipeline = RAGPipeline(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        logger.info("IndexerAgent inicializado")
    
    def index_directory(self, directory_path: str, 
                       file_types: List[str] = None,
                       clean_aggressive: bool = False) -> Dict[str, Any]:
        """
        Indexa todos los documentos de un directorio.
        
        Args:
            directory_path: Ruta del directorio
            file_types: Tipos de archivo a procesar
            clean_aggressive: Limpieza agresiva
            
        Returns:
            Estadísticas del proceso
        """
        logger.info(f"Iniciando indexación de: {directory_path}")
        
        stats = self.pipeline.index_directory(
            directory_path=directory_path,
            file_types=file_types or ['pdf', 'html', 'txt'],
            clean_aggressive=clean_aggressive,
            save_index=True
        )
        
        logger.info(f"Indexación completada: {stats}")
        return stats
    
    def load_existing_index(self):
        """Carga un índice existente."""
        logger.info("Cargando índice existente...")
        self.pipeline.load_existing_index()
        logger.info("Índice cargado exitosamente")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del índice."""
        return self.pipeline.get_stats()
    
    def add_documents(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Añade documentos adicionales al índice existente.
        
        Args:
            file_paths: Lista de rutas de archivos
            
        Returns:
            Estadísticas de la adición
        """
        logger.info(f"Añadiendo {len(file_paths)} documentos al índice...")
        
        # Cargar documentos
        documents = []
        for file_path in file_paths:
            path = Path(file_path)
            
            if path.suffix == '.pdf':
                docs = PDFLoaderTool.load_pdf(str(path))
                documents.extend(docs)
            elif path.suffix in ['.html', '.htm']:
                docs = HTMLLoaderTool.load_html(str(path))
                documents.extend(docs)
            elif path.suffix == '.txt':
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                doc = {
                    'content': content,
                    'metadata': {
                        'source': str(path),
                        'file_name': path.name,
                        'file_type': 'txt'
                    }
                }
                documents.append(doc)
        
        # Procesar y añadir
        stats = self.pipeline.process_and_index(documents, save_index=True)
        
        logger.info(f"Documentos añadidos: {stats}")
        return stats
