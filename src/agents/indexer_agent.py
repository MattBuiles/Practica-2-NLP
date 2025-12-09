"""
Agente Indexador - Implementación Persona 2.

Responsable del pipeline completo de indexación:
- Cargar documentos de múltiples formatos (PDF, HTML, TXT)
- Limpiar y normalizar texto
- Chunkear documentos con overlap
- Generar embeddings
- Indexar en FAISS
- Guardar índice persistente
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.tools.pdf_loader import PDFLoaderTool
from src.tools.html_loader import HTMLLoaderTool
from src.tools.text_loader import TextLoaderTool
from src.tools.text_cleaner import TextCleanerTool
from src.rag_pipeline.chunking import DocumentChunker
from src.rag_pipeline.embeddings import EmbeddingsManager
from src.rag_pipeline.vectorstore import VectorStoreManager
from src.config.paths import VECTORSTORE_DIR, VECTORSTORE_INDEX

logger = logging.getLogger(__name__)


class IndexerAgent:
    """
    Agente de Indexación.
    
    Implementación: Persona 2
    
    Pipeline completo de indexación:
    1. Cargar documentos (PDF, HTML, TXT)
    2. Limpiar y normalizar texto
    3. Chunkear con overlap
    4. Generar embeddings
    5. Indexar en FAISS
    6. Guardar índice persistente
    """
    
    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        """
        Inicializa el agente indexador.
        
        Args:
            chunk_size: Tamaño de chunks (default: desde settings.yaml)
            chunk_overlap: Overlap entre chunks (default: desde settings.yaml)
        """
        # Inicializar componentes del pipeline
        self.chunker = DocumentChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.embeddings_manager = EmbeddingsManager()
        self.vectorstore_manager = VectorStoreManager(index_name=VECTORSTORE_INDEX)
        
        logger.info("IndexerAgent inicializado correctamente")
    
    def index_directory(self, directory_path: str, 
                       file_types: List[str] = None,
                       clean_aggressive: bool = False,
                       save_index: bool = True) -> Dict[str, Any]:
        """
        Indexa todos los documentos de un directorio.
        
        Pipeline completo:
        1. Escanear directorio por tipos de archivo
        2. Cargar documentos con loaders apropiados
        3. Limpiar texto con TextCleanerTool
        4. Chunkear con DocumentChunker
        5. Generar embeddings con EmbeddingsManager
        6. Indexar en FAISS con VectorStoreManager
        7. Guardar índice persistente (opcional)
        
        Args:
            directory_path: Ruta del directorio
            file_types: Tipos de archivo a procesar ['pdf', 'html', 'txt'] (default: todos)
            clean_aggressive: Si aplicar limpieza agresiva
            save_index: Si guardar el índice en disco
            
        Returns:
            Estadísticas del proceso (documentos, chunks, etc.)
        """
        directory_path_obj = Path(directory_path)
        
        if not directory_path_obj.exists():
            logger.error(f"Directorio no existe: {directory_path}")
            return {
                "status": "error",
                "error": f"Directorio no existe: {directory_path}",
                "total_documents": 0,
                "total_chunks": 0
            }
        
        logger.info(f"Iniciando indexación de directorio: {directory_path}")
        
        # Tipos de archivo por defecto
        if file_types is None:
            file_types = ['pdf', 'html', 'txt']
        
        # Paso 1: Cargar documentos
        all_documents = []
        file_counts = {'pdf': 0, 'html': 0, 'txt': 0}
        
        try:
            # Cargar PDFs
            if 'pdf' in file_types:
                pdf_files = list(directory_path_obj.glob("*.pdf"))
                logger.info(f"Encontrados {len(pdf_files)} archivos PDF")
                for pdf_file in pdf_files:
                    try:
                        pdf_docs = PDFLoaderTool.load_pdf(str(pdf_file))
                        all_documents.extend(pdf_docs)
                        file_counts['pdf'] += len(pdf_docs)
                        logger.debug(f"Cargado PDF: {pdf_file.name} ({len(pdf_docs)} documentos)")
                    except Exception as e:
                        logger.warning(f"Error cargando PDF {pdf_file.name}: {e}")
            
            # Cargar HTMLs
            if 'html' in file_types:
                html_files = list(directory_path_obj.glob("*.html")) + list(directory_path_obj.glob("*.htm"))
                logger.info(f"Encontrados {len(html_files)} archivos HTML")
                for html_file in html_files:
                    try:
                        html_docs = HTMLLoaderTool.load_html(str(html_file))
                        all_documents.extend(html_docs)
                        file_counts['html'] += len(html_docs)
                        logger.debug(f"Cargado HTML: {html_file.name} ({len(html_docs)} documentos)")
                    except Exception as e:
                        logger.warning(f"Error cargando HTML {html_file.name}: {e}")
            
            # Cargar TXTs
            if 'txt' in file_types:
                txt_files = list(directory_path_obj.glob("*.txt"))
                logger.info(f"Encontrados {len(txt_files)} archivos TXT")
                for txt_file in txt_files:
                    try:
                        txt_docs = TextLoaderTool.load_text(str(txt_file))
                        all_documents.extend(txt_docs)
                        file_counts['txt'] += len(txt_docs)
                        logger.debug(f"Cargado TXT: {txt_file.name} ({len(txt_docs)} documentos)")
                    except Exception as e:
                        logger.warning(f"Error cargando TXT {txt_file.name}: {e}")
            
            logger.info(f"Total documentos cargados: {len(all_documents)}")
            
            if not all_documents:
                logger.warning("No se encontraron documentos para indexar")
                return {
                    "status": "warning",
                    "message": "No se encontraron documentos",
                    "total_documents": 0,
                    "total_chunks": 0,
                    "file_counts": file_counts
                }
            
            # Paso 2: Limpiar documentos
            logger.info("Limpiando documentos...")
            cleaned_docs = TextCleanerTool.clean_documents(
                all_documents,
                aggressive=clean_aggressive,
                min_length=50
            )
            logger.info(f"Documentos limpiados: {len(cleaned_docs)} (de {len(all_documents)} originales)")
            
            # Paso 3: Chunkear documentos
            logger.info("Chunking documentos...")
            chunks = self.chunker.chunk_documents(cleaned_docs)
            logger.info(f"Chunks generados: {len(chunks)}")
            
            # Paso 4: Generar embeddings
            logger.info("Generando embeddings...")
            chunks_with_embeddings = self.embeddings_manager.embed_documents(chunks)
            logger.info(f"Embeddings generados: {len(chunks_with_embeddings)}")
            
            # Paso 5: Crear índice FAISS
            logger.info("Creando índice FAISS...")
            success = self.vectorstore_manager.create_index(chunks_with_embeddings)
            
            if not success:
                logger.error("Error creando índice FAISS")
                return {
                    "status": "error",
                    "error": "Error creando índice FAISS",
                    "total_documents": len(cleaned_docs),
                    "total_chunks": len(chunks),
                    "file_counts": file_counts
                }
            
            # Paso 6: Guardar índice (opcional)
            if save_index:
                logger.info("Guardando índice en disco...")
                save_success = self.vectorstore_manager.save_index()
                if save_success:
                    logger.info("Índice guardado exitosamente")
                else:
                    logger.warning("Error guardando índice")
            
            # Estadísticas finales
            stats = self.vectorstore_manager.get_index_stats()
            
            result = {
                "status": "success",
                "total_documents": len(cleaned_docs),
                "total_chunks": len(chunks_with_embeddings),
                "cleaned_documents": len(cleaned_docs),
                "file_counts": file_counts,
                "directory": directory_path,
                "index_stats": stats,
                "save_index": save_index
            }
            
            logger.info(f"Indexación completada: {len(chunks_with_embeddings)} chunks indexados")
            return result
            
        except Exception as e:
            logger.error(f"Error en indexación: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "total_documents": len(all_documents),
                "total_chunks": 0,
                "file_counts": file_counts
            }
    
    def load_existing_index(self, index_path: Optional[str] = None) -> bool:
        """
        Carga un índice FAISS existente desde disco.
        
        Args:
            index_path: Ruta del índice (default: VECTORSTORE_DIR/VECTORSTORE_INDEX)
            
        Returns:
            True si se cargó exitosamente, False en caso contrario
        """
        try:
            if index_path is None:
                index_path = str(VECTORSTORE_DIR / VECTORSTORE_INDEX)
            
            logger.info(f"Cargando índice desde: {index_path}")
            success = self.vectorstore_manager.load_index(index_path)
            
            if success:
                logger.info("Índice cargado exitosamente")
                stats = self.vectorstore_manager.get_index_stats()
                logger.info(f"Índice contiene {stats.get('documents', 0)} documentos")
            else:
                logger.warning("No se pudo cargar el índice")
            
            return success
            
        except Exception as e:
            logger.error(f"Error cargando índice: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del índice actual.
        
        Returns:
            Estadísticas del índice (chunks, documentos, dimensión, etc.)
        """
        try:
            stats = self.vectorstore_manager.get_index_stats()
            
            # Agregar información adicional
            result = {
                "total_chunks": stats.get('documents', 0),
                "status": stats.get('status', 'unknown'),
                "embedding_dim": stats.get('embedding_dimension', 0),
                "index_name": stats.get('index_name', 'unknown'),
                "similarity_metric": stats.get('similarity_metric', 'unknown')
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {
                "total_chunks": 0,
                "status": "error",
                "error": str(e)
            }
    
    def add_documents(self, file_paths: List[str], 
                     clean_aggressive: bool = False,
                     save_index: bool = True) -> Dict[str, Any]:
        """
        Añade documentos adicionales al índice existente.
        
        Pipeline:
        1. Cargar nuevos documentos según tipo
        2. Limpiar y normalizar
        3. Chunkear
        4. Generar embeddings
        5. Agregar al índice FAISS existente
        6. Guardar cambios (opcional)
        
        Args:
            file_paths: Lista de rutas de archivos a añadir
            clean_aggressive: Si aplicar limpieza agresiva
            save_index: Si guardar el índice actualizado
            
        Returns:
            Estadísticas de la adición
        """
        if not file_paths:
            logger.warning("No se proporcionaron archivos para agregar")
            return {
                "status": "warning",
                "message": "No se proporcionaron archivos",
                "added_documents": 0,
                "added_chunks": 0
            }
        
        logger.info(f"Agregando {len(file_paths)} archivos al índice existente...")
        
        try:
            # Verificar que existe un índice
            stats_before = self.vectorstore_manager.get_index_stats()
            if stats_before.get('status') != 'active':
                logger.error("No hay índice activo. Usa index_directory() primero.")
                return {
                    "status": "error",
                    "error": "No hay índice activo",
                    "added_documents": 0,
                    "added_chunks": 0
                }
            
            # Paso 1: Cargar documentos
            all_documents = []
            for file_path in file_paths:
                file_path_obj = Path(file_path)
                
                if not file_path_obj.exists():
                    logger.warning(f"Archivo no existe: {file_path}")
                    continue
                
                try:
                    if file_path_obj.suffix.lower() == '.pdf':
                        docs = PDFLoaderTool.load_pdf(str(file_path_obj))
                    elif file_path_obj.suffix.lower() in ['.html', '.htm']:
                        docs = HTMLLoaderTool.load_html(str(file_path_obj))
                    elif file_path_obj.suffix.lower() == '.txt':
                        docs = TextLoaderTool.load_text(str(file_path_obj))
                    else:
                        logger.warning(f"Tipo de archivo no soportado: {file_path}")
                        continue
                    
                    all_documents.extend(docs)
                    logger.debug(f"Cargado: {file_path_obj.name} ({len(docs)} documentos)")
                    
                except Exception as e:
                    logger.warning(f"Error cargando {file_path}: {e}")
            
            if not all_documents:
                logger.warning("No se pudieron cargar documentos")
                return {
                    "status": "error",
                    "error": "No se pudieron cargar documentos",
                    "added_documents": 0,
                    "added_chunks": 0
                }
            
            # Paso 2: Limpiar
            logger.info("Limpiando documentos...")
            cleaned_docs = TextCleanerTool.clean_documents(
                all_documents,
                aggressive=clean_aggressive,
                min_length=50
            )
            
            # Paso 3: Chunkear
            logger.info("Chunking documentos...")
            chunks = self.chunker.chunk_documents(cleaned_docs)
            
            # Paso 4: Generar embeddings
            logger.info("Generando embeddings...")
            chunks_with_embeddings = self.embeddings_manager.embed_documents(chunks)
            
            # Paso 5: Agregar al índice
            logger.info("Agregando al índice FAISS...")
            success = self.vectorstore_manager.add_documents(chunks_with_embeddings)
            
            if not success:
                logger.error("Error agregando documentos al índice")
                return {
                    "status": "error",
                    "error": "Error agregando documentos",
                    "added_documents": len(cleaned_docs),
                    "added_chunks": len(chunks)
                }
            
            # Paso 6: Guardar (opcional)
            if save_index:
                logger.info("Guardando índice actualizado...")
                self.vectorstore_manager.save_index()
            
            # Estadísticas
            stats_after = self.vectorstore_manager.get_index_stats()
            chunks_before = stats_before.get('documents', 0)
            chunks_after = stats_after.get('documents', 0)
            
            result = {
                "status": "success",
                "added_documents": len(cleaned_docs),
                "added_chunks": len(chunks_with_embeddings),
                "chunks_before": chunks_before,
                "chunks_after": chunks_after,
                "total_chunks_now": chunks_after
            }
            
            logger.info(f"Documentos agregados: {len(chunks_with_embeddings)} chunks")
            return result
            
        except Exception as e:
            logger.error(f"Error agregando documentos: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "added_documents": 0,
                "added_chunks": 0
            }
