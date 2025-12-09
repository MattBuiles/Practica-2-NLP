"""
Módulo de compatibilidad para query_processing_tool.

Este módulo existe para mantener compatibilidad con tests que intentan
importar desde src.tools.query_processing_tool.

Las implementaciones reales están distribuidas en:
- document_search_tool.py
- query_optimizer_tool.py
- response_generator_tool.py
- validation_tool.py
- intent_classifier_tool.py
- logging_tool.py
"""

# Re-exportar todas las tools de query processing
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

# Aliases para compatibilidad
retrieve_documents = search_documents
generate_response = generate_rag_response

__all__ = [
    # Búsqueda
    'search_documents',
    'search_documents_by_metadata',
    'retrieve_documents',  # Alias
    
    # Optimización
    'optimize_search_query',
    
    # Generación
    'generate_rag_response',
    'generate_general_response',
    'generate_response',  # Alias
    
    # Validación
    'validate_response',
    'check_hallucination',
    
    # Clasificación
    'classify_intent',
    
    # Logging
    'log_agent_decision',
    'log_agent_action',
    'get_available_documents_info',
]
