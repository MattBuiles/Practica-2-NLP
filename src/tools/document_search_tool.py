"""
Tool de búsqueda semántica en el vector store.
LangChain Tool para que agentes autónomos puedan buscar documentos relevantes.
"""
import logging
from typing import List, Dict, Any
from langchain_core.tools import tool

from src.rag_pipeline.vectorstore import vectorstore_manager

logger = logging.getLogger(__name__)


@tool
def search_documents(query: str, k: int = 5, score_threshold: float = 0.0) -> List[Dict[str, Any]]:
    """
    Busca documentos relevantes en el vector store usando búsqueda semántica.
    
    Esta herramienta debe usarse cuando:
    - El usuario busca información específica sobre un tema
    - Se necesita encontrar documentos relevantes para una pregunta
    - Se requiere recuperar contexto para generar una respuesta
    - Se quiere comparar o resumir información de documentos
    
    Args:
        query: La consulta de búsqueda en lenguaje natural. 
               Ejemplo: "información sobre diabetes tipo 2"
        k: Número de documentos a recuperar (default: 5)
           Usa valores más altos (8-10) para resúmenes amplios
           Usa valores más bajos (3-5) para búsquedas específicas
        score_threshold: Umbral mínimo de similitud (0.0 a 1.0)
                        0.0 = devolver todos los k documentos
                        0.5+ = solo documentos muy relevantes
    
    Returns:
        Lista de documentos relevantes con su contenido y metadatos.
        Cada documento incluye: content, metadata (source, page, etc.), score
        
    Ejemplo de uso:
        # Buscar información específica
        docs = search_documents("síntomas de COVID-19", k=3)
        
        # Buscar para resumen amplio  
        docs = search_documents("tratamientos del cáncer", k=10)
    """
    try:
        if not vectorstore_manager.vectorstore:
            logger.error("Vector store no inicializado")
            return []
        
        logger.info(f"Buscando documentos para query: '{query}' (k={k}, threshold={score_threshold})")
        
        # Realizar búsqueda por similitud con scores
        results = vectorstore_manager.vectorstore.similarity_search_with_score(
            query, 
            k=k
        )
        
        # Filtrar por threshold y formatear resultados
        documents = []
        for doc, score in results:
            # Convertir score de distancia a similitud (FAISS usa distancia L2)
            # Score más bajo = más similar
            if score_threshold > 0.0:
                # Si hay threshold, filtrar documentos no relevantes
                # Normalizar score: 1 / (1 + distance)
                similarity = 1 / (1 + score)
                if similarity < score_threshold:
                    continue
            
            documents.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
                'score': float(score)
            })
        
        logger.info(f"Encontrados {len(documents)} documentos relevantes")
        return documents
        
    except Exception as e:
        logger.error(f"Error en búsqueda de documentos: {str(e)}")
        return []


@tool
def search_documents_by_metadata(metadata_filter: Dict[str, str], k: int = 5) -> List[Dict[str, Any]]:
    """
    Busca documentos filtrados por metadatos específicos.
    
    Esta herramienta debe usarse cuando:
    - Se necesita buscar en un documento específico por nombre
    - Se requiere filtrar por autor, fecha u otros metadatos
    - Se quiere comparar versiones o secciones específicas
    
    Args:
        metadata_filter: Diccionario con filtros de metadatos.
                        Ejemplo: {"source": "documento.pdf"}
                        Ejemplo: {"source": "articulo.html", "page": "1"}
        k: Número máximo de documentos a devolver (default: 5)
    
    Returns:
        Lista de documentos que coinciden con los filtros.
        
    Ejemplo de uso:
        # Buscar en documento específico
        docs = search_documents_by_metadata({"source": "diabetes.pdf"})
        
        # Buscar página específica
        docs = search_documents_by_metadata({"source": "manual.pdf", "page": "3"})
    """
    try:
        if not vectorstore_manager.vectorstore:
            logger.error("Vector store no inicializado")
            return []
        
        logger.info(f"Buscando documentos con filtros: {metadata_filter}")
        
        # FAISS no soporta filtrado nativo, hacemos búsqueda y filtramos manualmente
        # Primero hacemos una búsqueda amplia
        all_results = vectorstore_manager.vectorstore.similarity_search(
            "", 
            k=k * 10  # Buscar más documentos para filtrar
        )
        
        # Filtrar por metadatos
        filtered_docs = []
        for doc in all_results:
            match = True
            for key, value in metadata_filter.items():
                if key not in doc.metadata or str(doc.metadata[key]) != str(value):
                    match = False
                    break
            
            if match:
                filtered_docs.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': 0.0  # No hay score en filtrado directo
                })
                
                if len(filtered_docs) >= k:
                    break
        
        logger.info(f"Encontrados {len(filtered_docs)} documentos con filtros")
        return filtered_docs
        
    except Exception as e:
        logger.error(f"Error en búsqueda por metadatos: {str(e)}")
        return []
