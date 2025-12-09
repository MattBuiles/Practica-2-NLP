"""
Index Management Tool - LangChain Tool para gestionar índices vectoriales FAISS.

Esta herramienta permite a los agentes crear, actualizar, guardar y cargar
índices vectoriales de forma autónoma durante el proceso de indexación.
"""
import logging
from typing import List, Dict, Any
from langchain_core.tools import tool

from src.rag_pipeline.embeddings import EmbeddingsManager
from src.rag_pipeline.vectorstore import VectorStoreManager
from src.config.paths import VECTORSTORE_DIR, VECTORSTORE_INDEX

logger = logging.getLogger(__name__)


@tool
def create_vector_index(chunks: List[Dict[str, Any]], index_name: str = None) -> Dict[str, Any]:
    """
    Crea un nuevo índice vectorial FAISS a partir de chunks de documentos.
    
    **¿Cuándo usar esta herramienta?**
    - DESPUÉS de procesar documentos (limpiar + chunkear)
    - Cuando necesitas crear un índice desde cero
    - Para indexar una nueva colección de documentos
    - Al inicializar el sistema por primera vez
    
    **Casos de uso:**
    - "Crear índice vectorial con los chunks procesados"
    - "Inicializar FAISS con la colección de documentos"
    - "Generar embeddings e indexar"
    
    **Proceso interno:**
    1. Genera embeddings para cada chunk usando EmbeddingsManager
    2. Crea índice FAISS con los vectores
    3. Almacena metadata asociada a cada vector
    
    **IMPORTANTE:** Esta herramienta REEMPLAZA cualquier índice existente con el mismo nombre.
    Si quieres agregar a un índice existente, usa 'add_to_vector_index' en su lugar.
    
    Args:
        chunks: Lista de chunks a indexar (con 'content' y 'metadata')
        index_name: Nombre del índice (default: usa VECTORSTORE_INDEX de config)
        
    Returns:
        Dict con:
        - status: "success" o "error"
        - total_chunks: Cantidad de chunks indexados
        - embedding_dimension: Dimensión de los vectores
        - index_name: Nombre del índice creado
        - index_stats: Estadísticas del índice (documentos, métrica, etc.)
        
    Example:
        >>> chunks = process_documents_pipeline(docs)['final_chunks']
        >>> result = create_vector_index(chunks)
        >>> print(f"Indexados {result['total_chunks']} chunks")
        Indexados 150 chunks
    """
    try:
        if not chunks:
            return {
                "status": "error",
                "error": "No se proporcionaron chunks para indexar",
                "total_chunks": 0
            }
        
        if index_name is None:
            index_name = VECTORSTORE_INDEX
        
        logger.info(f"Creando índice vectorial '{index_name}' con {len(chunks)} chunks")
        
        # Inicializar componentes
        embeddings_manager = EmbeddingsManager()
        vectorstore_manager = VectorStoreManager(index_name=index_name)
        
        # Paso 1: Generar embeddings
        logger.info("Generando embeddings...")
        chunks_with_embeddings = embeddings_manager.embed_documents(chunks)
        
        if not chunks_with_embeddings:
            return {
                "status": "error",
                "error": "No se pudieron generar embeddings",
                "total_chunks": 0
            }
        
        # Paso 2: Crear índice FAISS
        logger.info("Creando índice FAISS...")
        success = vectorstore_manager.create_index(chunks_with_embeddings)
        
        if not success:
            return {
                "status": "error",
                "error": "Error creando índice FAISS",
                "total_chunks": len(chunks)
            }
        
        # Obtener estadísticas
        stats = vectorstore_manager.get_index_stats()
        
        logger.info(f"Índice creado exitosamente: {len(chunks_with_embeddings)} chunks")
        
        return {
            "status": "success",
            "total_chunks": len(chunks_with_embeddings),
            "embedding_dimension": stats.get('embedding_dimension', 0),
            "index_name": index_name,
            "index_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error creando índice vectorial: {e}")
        return {
            "status": "error",
            "error": str(e),
            "total_chunks": len(chunks) if chunks else 0
        }


@tool
def add_to_vector_index(chunks: List[Dict[str, Any]], index_name: str = None) -> Dict[str, Any]:
    """
    Agrega chunks adicionales a un índice vectorial existente.
    
    **¿Cuándo usar esta herramienta?**
    - Cuando YA existe un índice y quieres agregar más documentos
    - Para actualización incremental del índice
    - Al agregar documentos nuevos sin reindexar todo
    - Cuando recibes documentos adicionales después de la indexación inicial
    
    **Casos de uso:**
    - "Agregar estos nuevos documentos al índice existente"
    - "Actualizar índice con documentos recientes"
    - "Indexar documentos adicionales sin perder los anteriores"
    
    **IMPORTANTE:** 
    - Requiere que exista un índice activo previamente cargado
    - Si no existe índice, usa 'create_vector_index' primero
    
    Args:
        chunks: Lista de chunks nuevos a agregar
        index_name: Nombre del índice (default: usa VECTORSTORE_INDEX de config)
        
    Returns:
        Dict con:
        - status: "success" o "error"
        - added_chunks: Cantidad de chunks agregados
        - chunks_before: Cantidad de chunks antes de agregar
        - chunks_after: Cantidad total después de agregar
        - index_name: Nombre del índice actualizado
        
    Example:
        >>> new_chunks = process_documents_pipeline(new_docs)['final_chunks']
        >>> result = add_to_vector_index(new_chunks)
        >>> print(f"Agregados {result['added_chunks']} chunks")
        Agregados 25 chunks
        >>> print(f"Total ahora: {result['chunks_after']}")
        Total ahora: 175
    """
    try:
        if not chunks:
            return {
                "status": "error",
                "error": "No se proporcionaron chunks para agregar",
                "added_chunks": 0
            }
        
        if index_name is None:
            index_name = VECTORSTORE_INDEX
        
        logger.info(f"Agregando {len(chunks)} chunks al índice '{index_name}'")
        
        # Inicializar componentes
        embeddings_manager = EmbeddingsManager()
        vectorstore_manager = VectorStoreManager(index_name=index_name)
        
        # Verificar índice existente
        stats_before = vectorstore_manager.get_index_stats()
        if stats_before.get('status') != 'active':
            return {
                "status": "error",
                "error": "No hay índice activo. Usa create_vector_index primero",
                "added_chunks": 0
            }
        
        chunks_before = stats_before.get('documents', 0)
        
        # Generar embeddings
        logger.info("Generando embeddings para nuevos chunks...")
        chunks_with_embeddings = embeddings_manager.embed_documents(chunks)
        
        # Agregar al índice
        logger.info("Agregando al índice FAISS...")
        success = vectorstore_manager.add_documents(chunks_with_embeddings)
        
        if not success:
            return {
                "status": "error",
                "error": "Error agregando documentos al índice",
                "added_chunks": 0,
                "chunks_before": chunks_before
            }
        
        # Estadísticas actualizadas
        stats_after = vectorstore_manager.get_index_stats()
        chunks_after = stats_after.get('documents', 0)
        
        logger.info(f"Chunks agregados: {len(chunks_with_embeddings)} (total: {chunks_after})")
        
        return {
            "status": "success",
            "added_chunks": len(chunks_with_embeddings),
            "chunks_before": chunks_before,
            "chunks_after": chunks_after,
            "index_name": index_name
        }
        
    except Exception as e:
        logger.error(f"Error agregando chunks al índice: {e}")
        return {
            "status": "error",
            "error": str(e),
            "added_chunks": 0
        }


@tool
def save_vector_index(index_name: str = None, save_path: str = None) -> Dict[str, Any]:
    """
    Guarda el índice vectorial actual en disco para persistencia.
    
    **¿Cuándo usar esta herramienta?**
    - DESPUÉS de crear o actualizar un índice
    - Para persistir el índice y no perder el trabajo
    - Al finalizar el proceso de indexación
    - Antes de cerrar la sesión o reiniciar el sistema
    
    **Casos de uso:**
    - "Guardar el índice en disco"
    - "Persistir índice para uso futuro"
    - "Hacer backup del índice actual"
    
    **Ubicación por defecto:**
    - Path: data/vectorstore/faiss_index/
    - Archivos generados: index.faiss, index.pkl
    
    Args:
        index_name: Nombre del índice (default: usa VECTORSTORE_INDEX de config)
        save_path: Ruta personalizada (default: usa VECTORSTORE_DIR de config)
        
    Returns:
        Dict con:
        - status: "success" o "error"
        - index_name: Nombre del índice guardado
        - save_path: Ruta donde se guardó
        - file_count: Cantidad de archivos creados
        - total_chunks: Cantidad de chunks en el índice
        
    Example:
        >>> result = save_vector_index()
        >>> print(f"Índice guardado en: {result['save_path']}")
        Índice guardado en: data/vectorstore/faiss_index
    """
    try:
        if index_name is None:
            index_name = VECTORSTORE_INDEX
        
        if save_path is None:
            save_path = str(VECTORSTORE_DIR)
        
        logger.info(f"Guardando índice '{index_name}' en {save_path}")
        
        vectorstore_manager = VectorStoreManager(index_name=index_name)
        
        # Verificar índice activo
        stats = vectorstore_manager.get_index_stats()
        if stats.get('status') != 'active':
            return {
                "status": "error",
                "error": "No hay índice activo para guardar",
                "index_name": index_name
            }
        
        # Guardar índice
        success = vectorstore_manager.save_index(save_path)
        
        if not success:
            return {
                "status": "error",
                "error": "Error guardando índice en disco",
                "index_name": index_name
            }
        
        total_chunks = stats.get('documents', 0)
        
        logger.info(f"Índice guardado exitosamente: {total_chunks} chunks")
        
        return {
            "status": "success",
            "index_name": index_name,
            "save_path": save_path,
            "file_count": 2,  # index.faiss y index.pkl
            "total_chunks": total_chunks
        }
        
    except Exception as e:
        logger.error(f"Error guardando índice: {e}")
        return {
            "status": "error",
            "error": str(e),
            "index_name": index_name or "unknown"
        }


@tool
def load_vector_index(index_name: str = None, load_path: str = None) -> Dict[str, Any]:
    """
    Carga un índice vectorial existente desde disco a memoria.
    
    **¿Cuándo usar esta herramienta?**
    - Al iniciar el sistema cuando ya existe un índice guardado
    - ANTES de hacer búsquedas en el vectorstore
    - Cuando necesitas usar un índice previamente creado
    - Para restaurar un índice después de reiniciar
    
    **Casos de uso:**
    - "Cargar el índice existente para consultas"
    - "Restaurar índice guardado"
    - "Inicializar vectorstore desde disco"
    
    **IMPORTANTE:** 
    - Si no existe el archivo, retorna error
    - Usa esta herramienta ANTES de add_to_vector_index
    
    Args:
        index_name: Nombre del índice (default: usa VECTORSTORE_INDEX de config)
        load_path: Ruta del índice (default: usa VECTORSTORE_DIR de config)
        
    Returns:
        Dict con:
        - status: "success" o "error"
        - index_name: Nombre del índice cargado
        - load_path: Ruta desde donde se cargó
        - total_chunks: Cantidad de chunks en el índice
        - embedding_dimension: Dimensión de vectores
        - index_stats: Estadísticas completas del índice
        
    Example:
        >>> result = load_vector_index()
        >>> print(f"Índice cargado: {result['total_chunks']} chunks")
        Índice cargado: 150 chunks
    """
    try:
        if index_name is None:
            index_name = VECTORSTORE_INDEX
        
        if load_path is None:
            load_path = str(VECTORSTORE_DIR / index_name)
        
        logger.info(f"Cargando índice '{index_name}' desde {load_path}")
        
        vectorstore_manager = VectorStoreManager(index_name=index_name)
        
        # Cargar índice
        success = vectorstore_manager.load_index(load_path)
        
        if not success:
            return {
                "status": "error",
                "error": f"No se pudo cargar índice desde {load_path}",
                "index_name": index_name
            }
        
        # Obtener estadísticas
        stats = vectorstore_manager.get_index_stats()
        total_chunks = stats.get('documents', 0)
        
        logger.info(f"Índice cargado exitosamente: {total_chunks} chunks")
        
        return {
            "status": "success",
            "index_name": index_name,
            "load_path": load_path,
            "total_chunks": total_chunks,
            "embedding_dimension": stats.get('embedding_dimension', 0),
            "index_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error cargando índice: {e}")
        return {
            "status": "error",
            "error": str(e),
            "index_name": index_name or "unknown"
        }


@tool
def get_index_statistics(index_name: str = None) -> Dict[str, Any]:
    """
    Obtiene estadísticas detalladas del índice vectorial actual.
    
    **¿Cuándo usar esta herramienta?**
    - Para verificar el estado del índice antes de operar
    - Para validar que el índice está cargado correctamente
    - Para reportar progreso de indexación
    - Para debugging y monitoreo
    
    **Casos de uso:**
    - "¿Cuántos documentos hay indexados?"
    - "Verificar si el índice está activo"
    - "Obtener dimensión de embeddings del índice"
    
    Args:
        index_name: Nombre del índice (default: usa VECTORSTORE_INDEX de config)
        
    Returns:
        Dict con:
        - status: "active", "empty", o "error"
        - total_chunks: Cantidad de chunks indexados
        - embedding_dimension: Dimensión de los vectores
        - similarity_metric: Métrica usada (típicamente "cosine")
        - index_name: Nombre del índice
        - has_index: Boolean indicando si existe índice activo
        
    Example:
        >>> stats = get_index_statistics()
        >>> if stats['status'] == 'active':
        ...     print(f"Índice OK: {stats['total_chunks']} chunks")
    """
    try:
        if index_name is None:
            index_name = VECTORSTORE_INDEX
        
        vectorstore_manager = VectorStoreManager(index_name=index_name)
        
        stats = vectorstore_manager.get_index_stats()
        
        # Enriquecer con información adicional
        result = {
            "status": stats.get('status', 'unknown'),
            "total_chunks": stats.get('documents', 0),
            "embedding_dimension": stats.get('embedding_dimension', 0),
            "similarity_metric": stats.get('similarity_metric', 'unknown'),
            "index_name": stats.get('index_name', index_name),
            "has_index": stats.get('status') == 'active'
        }
        
        logger.info(f"Estadísticas del índice: {result['total_chunks']} chunks, status={result['status']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return {
            "status": "error",
            "error": str(e),
            "total_chunks": 0,
            "has_index": False
        }
