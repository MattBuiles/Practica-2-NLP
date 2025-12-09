"""
Módulo de herramientas del sistema.
Incluye tools clásicas (loaders) y LangChain tools (@tool) para agentes autónomos.
"""
import logging

# Tools clásicas para procesamiento de documentos
from .pdf_loader import PDFLoaderTool
from .html_loader import HTMLLoaderTool
from .text_loader import TextLoaderTool
from .text_cleaner import TextCleanerTool
from .trace_exporter import TraceExporterTool

# LangChain Tools para agentes autónomos
from .document_search_tool import (
    search_documents,
    search_documents_by_metadata
)
from .query_optimizer_tool import optimize_search_query
from .response_generator_tool import (
    generate_rag_response,
    generate_general_response
)
from .validation_tool import (
    validate_response,
    check_hallucination
)
from .intent_classifier_tool import classify_intent
from .logging_tool import (
    log_agent_decision,
    log_agent_action,
    get_available_documents_info
)

# Aliases para compatibilidad con nombres esperados
retrieve_documents = search_documents  # Alias
generate_response = generate_rag_response  # Alias

# Indexer Tools
from .document_loader_tool import (
    load_document,
    scan_directory_for_documents,
    load_documents_batch
)
from .document_processing_tool import (
    clean_documents,
    chunk_documents,
    process_documents_pipeline
)
from .index_management_tool import (
    create_vector_index,
    add_to_vector_index,
    save_vector_index,
    load_vector_index,
    get_index_statistics
)

logger = logging.getLogger(__name__)

__all__ = [
    # Tools clásicas
    'PDFLoaderTool',
    'HTMLLoaderTool',
    'TextLoaderTool',
    'TextCleanerTool',
    'TraceExporterTool',
    
    # LangChain Tools - Query Processing
    'search_documents',
    'search_documents_by_metadata',
    'optimize_search_query',
    'generate_rag_response',
    'generate_general_response',
    'validate_response',
    'check_hallucination',
    'classify_intent',
    'log_agent_decision',
    'log_agent_action',
    'get_available_documents_info',
    
    # Aliases para compatibilidad
    'retrieve_documents',
    'generate_response',
    
    # LangChain Tools - Indexing
    'load_document',
    'scan_directory_for_documents',
    'load_documents_batch',
    'clean_documents',
    'chunk_documents',
    'process_documents_pipeline',
    'create_vector_index',
    'add_to_vector_index',
    'save_vector_index',
    'load_vector_index',
    'get_index_statistics',
]

# Lista de todas las LangChain tools disponibles para agentes
ALL_LANGCHAIN_TOOLS = [
    # Búsqueda y recuperación
    search_documents,
    search_documents_by_metadata,
    optimize_search_query,
    
    # Generación de respuestas
    generate_rag_response,
    generate_general_response,
    
    # Validación
    validate_response,
    check_hallucination,
    
    # Clasificación
    classify_intent,
    
    # Logging y trazabilidad
    log_agent_decision,
    log_agent_action,
    get_available_documents_info,
    
    # Indexing - Document Loading
    load_document,
    scan_directory_for_documents,
    load_documents_batch,
    
    # Indexing - Document Processing
    clean_documents,
    chunk_documents,
    process_documents_pipeline,
    
    # Indexing - Index Management
    create_vector_index,
    add_to_vector_index,
    save_vector_index,
    load_vector_index,
    get_index_statistics,
]

# Tools por categoría para asignación específica a agentes
RETRIEVER_TOOLS = [
    search_documents,
    search_documents_by_metadata,
    optimize_search_query,
    log_agent_action,
]

RAG_TOOLS = [
    generate_rag_response,
    generate_general_response,
    log_agent_action,
]

CRITIC_TOOLS = [
    validate_response,
    check_hallucination,
    log_agent_decision,
]

CLASSIFIER_TOOLS = [
    classify_intent,
    get_available_documents_info,
    log_agent_decision,
]

INDEXER_TOOLS = [
    # Document Loading
    scan_directory_for_documents,
    load_document,
    load_documents_batch,
    
    # Document Processing
    clean_documents,
    chunk_documents,
    process_documents_pipeline,
    
    # Index Management
    create_vector_index,
    add_to_vector_index,
    save_vector_index,
    load_vector_index,
    get_index_statistics,
    
    # Logging
    log_agent_decision,
    log_agent_action,
]

logger.info(f"Tools cargadas: {len(ALL_LANGCHAIN_TOOLS)} LangChain tools disponibles")
