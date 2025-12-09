"""
Pipeline RAG completo.
Implementación: Persona 2

Orquesta IndexerAgent y VectorStoreManager para proporcionar
una interfaz de alto nivel para indexación y búsqueda.
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.agents.indexer_agent import IndexerAgent
from src.rag_pipeline.vectorstore import VectorStoreManager
from src.config.paths import VECTORSTORE_DIR, VECTORSTORE_INDEX

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Pipeline RAG completo.
    
    Implementación: Persona 2
    
    Orquesta los componentes del pipeline RAG:
    - IndexerAgent: Para indexación de documentos
    - VectorStoreManager: Para búsqueda semántica
    
    Proporciona una interfaz de alto nivel para:
    - Indexar directorios de documentos
    - Cargar índices existentes
    - Realizar búsquedas semánticas
    """
    
    def __init__(self):
        """
        Inicializa el pipeline RAG.
        
        Crea instancias de IndexerAgent y VectorStoreManager.
        """
        logger.info("Inicializando RAGPipeline...")
        
        self.indexer = IndexerAgent()
        self.vectorstore = VectorStoreManager(index_name=VECTORSTORE_INDEX)
        
        logger.info("RAGPipeline inicializado correctamente")
    
    def index_directory(self, 
                       directory_path: str,
                       file_types: List[str] = None,
                       clean_aggressive: bool = False,
                       save_index: bool = True) -> Dict[str, Any]:
        """
        Indexa todos los documentos de un directorio.
        
        Usa IndexerAgent para ejecutar el pipeline completo:
        1. Cargar documentos (PDF, HTML, TXT)
        2. Limpiar y normalizar
        3. Chunkear con overlap
        4. Generar embeddings
        5. Indexar en FAISS
        6. Guardar índice (opcional)
        
        Args:
            directory_path: Ruta del directorio con documentos
            file_types: Tipos de archivo a procesar ['pdf', 'html', 'txt'] (default: todos)
            clean_aggressive: Si aplicar limpieza agresiva
            save_index: Si guardar el índice en disco
            
        Returns:
            Estadísticas del proceso de indexación
        """
        logger.info(f"Indexando directorio: {directory_path}")
        
        # Delegar a IndexerAgent
        stats = self.indexer.index_directory(
            directory_path=directory_path,
            file_types=file_types,
            clean_aggressive=clean_aggressive,
            save_index=save_index
        )
        
        # Actualizar referencia al vectorstore del indexer
        self.vectorstore = self.indexer.vectorstore_manager
        
        logger.info(f"Indexación completada: {stats.get('status')}")
        return stats
    
    def load_existing_index(self, index_path: Optional[str] = None) -> bool:
        """
        Carga un índice FAISS existente desde disco.
        
        Args:
            index_path: Ruta del índice (default: VECTORSTORE_DIR/VECTORSTORE_INDEX)
            
        Returns:
            True si se cargó exitosamente, False en caso contrario
        """
        logger.info("Cargando índice existente...")
        
        # Intentar cargar con IndexerAgent
        success = self.indexer.load_existing_index(index_path)
        
        if success:
            # Actualizar referencia al vectorstore
            self.vectorstore = self.indexer.vectorstore_manager
            logger.info("Índice cargado exitosamente")
        else:
            # Intentar cargar directamente con VectorStoreManager
            logger.info("Intentando cargar directamente con VectorStoreManager...")
            if index_path is None:
                index_path = str(VECTORSTORE_DIR / VECTORSTORE_INDEX)
            success = self.vectorstore.load_index(index_path)
            
            if success:
                logger.info("Índice cargado exitosamente")
            else:
                logger.warning("No se pudo cargar el índice")
        
        return success
    
    def query(self, query: str, k: int = 5, 
              score_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Realiza una búsqueda semántica en el índice.
        
        Args:
            query: Texto de consulta
            k: Número de documentos a recuperar
            score_threshold: Umbral mínimo de similitud (None = no filtrar)
            
        Returns:
            Lista de documentos relevantes con formato:
            {'content': str, 'metadata': dict, 'score': float}
        """
        logger.info(f"Buscando: '{query[:50]}...' (k={k})")
        
        # Verificar que hay un índice cargado
        stats = self.vectorstore.get_index_stats()
        if stats.get('status') != 'active':
            logger.warning("No hay índice activo. Cargando índice existente...")
            if not self.load_existing_index():
                logger.error("No se pudo cargar el índice. Indexa documentos primero.")
                return []
        
        # Realizar búsqueda
        results = self.vectorstore.similarity_search(
            query=query,
            k=k,
            score_threshold=score_threshold
        )
        
        logger.info(f"Búsqueda completada: {len(results)} resultados")
        return results
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del índice actual.
        
        Returns:
            Diccionario con estadísticas del índice
        """
        return self.indexer.get_index_stats()
    
    def add_documents(self, 
                     file_paths: List[str],
                     clean_aggressive: bool = False,
                     save_index: bool = True) -> Dict[str, Any]:
        """
        Agrega documentos adicionales al índice existente.
        
        Args:
            file_paths: Lista de rutas de archivos a agregar
            clean_aggressive: Si aplicar limpieza agresiva
            save_index: Si guardar el índice actualizado
            
        Returns:
            Estadísticas de la adición
        """
        logger.info(f"Agregando {len(file_paths)} archivos al índice...")
        
        stats = self.indexer.add_documents(
            file_paths=file_paths,
            clean_aggressive=clean_aggressive,
            save_index=save_index
        )
        
        # Actualizar referencia al vectorstore
        self.vectorstore = self.indexer.vectorstore_manager
        
        return stats
