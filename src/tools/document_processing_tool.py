"""
Document Processing Tool - LangChain Tool para procesar documentos (limpieza y chunking).

Esta herramienta permite a los agentes limpiar, normalizar y dividir documentos
en chunks de forma autónoma durante el proceso de indexación.
"""
import logging
from typing import List, Dict, Any
from langchain_core.tools import tool

from src.tools.text_cleaner import TextCleanerTool
from src.rag_pipeline.chunking import DocumentChunker

logger = logging.getLogger(__name__)


@tool
def clean_documents(documents: List[Dict[str, Any]], aggressive: bool = False, min_length: int = 50) -> Dict[str, Any]:
    """
    Limpia y normaliza el contenido de documentos removiendo ruido y estandarizando formato.
    
    **¿Cuándo usar esta herramienta?**
    - DESPUÉS de cargar documentos y ANTES de chunkear
    - Cuando los documentos tienen ruido (HTML tags, caracteres especiales, etc.)
    - Para estandarizar formato de texto antes de embeddings
    - Cuando necesitas filtrar documentos muy cortos o vacíos
    
    **Casos de uso:**
    - "Los documentos HTML tienen muchos tags, necesito limpiarlos"
    - "Normalizar espacios y saltos de línea en los textos"
    - "Remover documentos demasiado cortos que no aportan información"
    
    **Modo aggressive:**
    - False (default): Limpieza básica (espacios, saltos de línea, caracteres especiales básicos)
    - True: Limpieza agresiva (remueve URLs, emails, números sueltos, etc.)
    
    Args:
        documents: Lista de documentos a limpiar (cada uno con 'content' y 'metadata')
        aggressive: Si aplicar limpieza agresiva (default: False)
        min_length: Longitud mínima de contenido para mantener documento (default: 50)
        
    Returns:
        Dict con:
        - status: "success" o "error"
        - cleaned_documents: Lista de documentos limpiados
        - original_count: Cantidad de documentos originales
        - cleaned_count: Cantidad de documentos después de limpieza
        - removed_count: Cantidad de documentos removidos por ser muy cortos
        - cleaning_mode: "basic" o "aggressive"
        
    Example:
        >>> docs = [{"content": "Texto sucio  con   espacios", "metadata": {}}]
        >>> result = clean_documents(docs, aggressive=False)
        >>> print(result['cleaned_documents'][0]['content'])
        'Texto sucio con espacios'
    """
    try:
        if not documents:
            return {
                "status": "error",
                "error": "No se proporcionaron documentos",
                "cleaned_documents": [],
                "original_count": 0,
                "cleaned_count": 0
            }
        
        logger.info(f"Limpiando {len(documents)} documentos (aggressive={aggressive}, min_length={min_length})")
        
        # Usar TextCleanerTool existente
        cleaned_docs = TextCleanerTool.clean_documents(
            documents=documents,
            aggressive=aggressive,
            min_length=min_length
        )
        
        original_count = len(documents)
        cleaned_count = len(cleaned_docs)
        removed_count = original_count - cleaned_count
        
        logger.info(f"Limpieza completada: {cleaned_count}/{original_count} documentos (removidos: {removed_count})")
        
        return {
            "status": "success",
            "cleaned_documents": cleaned_docs,
            "original_count": original_count,
            "cleaned_count": cleaned_count,
            "removed_count": removed_count,
            "cleaning_mode": "aggressive" if aggressive else "basic"
        }
        
    except Exception as e:
        logger.error(f"Error limpiando documentos: {e}")
        return {
            "status": "error",
            "error": str(e),
            "cleaned_documents": [],
            "original_count": len(documents) if documents else 0,
            "cleaned_count": 0
        }


@tool
def chunk_documents(documents: List[Dict[str, Any]], chunk_size: int = None, chunk_overlap: int = None) -> Dict[str, Any]:
    """
    Divide documentos en chunks (fragmentos) de tamaño controlado con overlap para contexto.
    
    **¿Cuándo usar esta herramienta?**
    - DESPUÉS de limpiar documentos y ANTES de generar embeddings
    - Cuando los documentos son muy largos para procesamiento de embeddings
    - Para crear chunks con overlap que mantengan contexto entre fragmentos
    - Cuando necesitas chunks de tamaño específico para tu modelo de embeddings
    
    **Casos de uso:**
    - "Los documentos son muy largos, dividirlos en chunks"
    - "Necesito chunks de 500 tokens con overlap de 50"
    - "Preparar documentos para generación de embeddings"
    
    **Parámetros importantes:**
    - chunk_size: Tamaño máximo de cada chunk (default: desde settings.yaml, típicamente 1000)
    - chunk_overlap: Cantidad de tokens que se solapan entre chunks (default: desde settings.yaml, típicamente 200)
    
    **Estrategia de chunking:**
    - Respeta límites de oraciones cuando es posible
    - Mantiene metadata del documento original
    - Agrega información de chunk_index para trazabilidad
    
    Args:
        documents: Lista de documentos a chunkear
        chunk_size: Tamaño máximo de chunk en tokens (None usa default de settings)
        chunk_overlap: Overlap entre chunks (None usa default de settings)
        
    Returns:
        Dict con:
        - status: "success" o "error"
        - chunks: Lista de chunks generados
        - original_documents: Cantidad de documentos originales
        - total_chunks: Cantidad total de chunks generados
        - avg_chunks_per_doc: Promedio de chunks por documento
        - chunk_size_used: Tamaño de chunk usado
        - chunk_overlap_used: Overlap usado
        
    Example:
        >>> docs = [{"content": "Texto muy largo...", "metadata": {"source": "doc1.pdf"}}]
        >>> result = chunk_documents(docs, chunk_size=500, chunk_overlap=50)
        >>> print(f"Generados {result['total_chunks']} chunks")
        Generados 3 chunks
    """
    try:
        if not documents:
            return {
                "status": "error",
                "error": "No se proporcionaron documentos",
                "chunks": [],
                "original_documents": 0,
                "total_chunks": 0
            }
        
        logger.info(f"Chunking {len(documents)} documentos (size={chunk_size}, overlap={chunk_overlap})")
        
        # Crear chunker con parámetros específicos o defaults
        chunker = DocumentChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Chunkear documentos
        chunks = chunker.chunk_documents(documents)
        
        avg_chunks = len(chunks) / len(documents) if documents else 0
        
        logger.info(f"Chunking completado: {len(chunks)} chunks generados ({avg_chunks:.1f} por documento)")
        
        return {
            "status": "success",
            "chunks": chunks,
            "original_documents": len(documents),
            "total_chunks": len(chunks),
            "avg_chunks_per_doc": round(avg_chunks, 2),
            "chunk_size_used": chunker.chunk_size,
            "chunk_overlap_used": chunker.chunk_overlap
        }
        
    except Exception as e:
        logger.error(f"Error chunking documentos: {e}")
        return {
            "status": "error",
            "error": str(e),
            "chunks": [],
            "original_documents": len(documents) if documents else 0,
            "total_chunks": 0
        }


@tool
def process_documents_pipeline(documents: List[Dict[str, Any]], 
                               clean_aggressive: bool = False,
                               min_length: int = 50,
                               chunk_size: int = None,
                               chunk_overlap: int = None) -> Dict[str, Any]:
    """
    Ejecuta el pipeline completo de procesamiento: limpieza + chunking en un solo paso.
    
    **¿Cuándo usar esta herramienta?**
    - Cuando quieres procesar documentos de forma eficiente en un paso
    - Para ejecutar limpieza y chunking con configuración estándar
    - Cuando no necesitas inspeccionar resultados intermedios
    - Para procesamiento rápido de lotes de documentos
    
    **Casos de uso:**
    - "Procesar estos documentos de principio a fin"
    - "Necesito chunks listos para embeddings de forma rápida"
    - "Pipeline estándar de procesamiento"
    
    **Ventajas vs pasos separados:**
    - Más eficiente (menos llamadas de herramientas)
    - Configuración consistente
    - Menos oportunidad de errores entre pasos
    
    **Desventajas vs pasos separados:**
    - Menos control sobre pasos intermedios
    - No puedes ajustar parámetros entre limpieza y chunking
    
    Args:
        documents: Lista de documentos a procesar
        clean_aggressive: Si aplicar limpieza agresiva
        min_length: Longitud mínima para mantener documentos
        chunk_size: Tamaño de chunks (None usa default)
        chunk_overlap: Overlap entre chunks (None usa default)
        
    Returns:
        Dict con:
        - status: "success" o "error"
        - final_chunks: Chunks listos para embeddings
        - original_documents: Cantidad inicial
        - cleaned_documents: Cantidad después de limpieza
        - removed_documents: Cantidad removida en limpieza
        - total_chunks: Cantidad final de chunks
        - pipeline_summary: Resumen del proceso completo
        
    Example:
        >>> docs = load_documents_batch(["doc1.pdf", "doc2.html"])['documents']
        >>> result = process_documents_pipeline(docs, clean_aggressive=True)
        >>> chunks = result['final_chunks']  # Listos para embeddings
    """
    try:
        if not documents:
            return {
                "status": "error",
                "error": "No se proporcionaron documentos",
                "final_chunks": [],
                "original_documents": 0
            }
        
        logger.info(f"Pipeline de procesamiento: {len(documents)} documentos")
        
        # Paso 1: Limpiar
        clean_result = clean_documents.invoke({
            "documents": documents,
            "aggressive": clean_aggressive,
            "min_length": min_length
        })
        
        if clean_result["status"] != "success":
            return {
                "status": "error",
                "error": f"Error en limpieza: {clean_result.get('error')}",
                "final_chunks": [],
                "original_documents": len(documents)
            }
        
        cleaned_docs = clean_result["cleaned_documents"]
        
        if not cleaned_docs:
            return {
                "status": "error",
                "error": "Todos los documentos fueron removidos durante limpieza",
                "final_chunks": [],
                "original_documents": len(documents),
                "cleaned_documents": 0
            }
        
        # Paso 2: Chunkear
        chunk_result = chunk_documents.invoke({
            "documents": cleaned_docs,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap
        })
        
        if chunk_result["status"] != "success":
            return {
                "status": "error",
                "error": f"Error en chunking: {chunk_result.get('error')}",
                "final_chunks": [],
                "original_documents": len(documents),
                "cleaned_documents": len(cleaned_docs)
            }
        
        chunks = chunk_result["chunks"]
        
        # Resumen del pipeline
        pipeline_summary = {
            "step_1_cleaning": {
                "input": len(documents),
                "output": len(cleaned_docs),
                "removed": clean_result["removed_count"],
                "mode": clean_result["cleaning_mode"]
            },
            "step_2_chunking": {
                "input": len(cleaned_docs),
                "output": len(chunks),
                "chunk_size": chunk_result["chunk_size_used"],
                "chunk_overlap": chunk_result["chunk_overlap_used"]
            }
        }
        
        logger.info(f"Pipeline completado: {len(documents)} docs -> {len(chunks)} chunks")
        
        return {
            "status": "success",
            "final_chunks": chunks,
            "original_documents": len(documents),
            "cleaned_documents": len(cleaned_docs),
            "removed_documents": clean_result["removed_count"],
            "total_chunks": len(chunks),
            "pipeline_summary": pipeline_summary
        }
        
    except Exception as e:
        logger.error(f"Error en pipeline de procesamiento: {e}")
        return {
            "status": "error",
            "error": str(e),
            "final_chunks": [],
            "original_documents": len(documents) if documents else 0
        }
