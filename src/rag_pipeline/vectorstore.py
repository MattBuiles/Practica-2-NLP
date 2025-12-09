"""
Gestión del vector store FAISS.
Implementación: Persona 2

Gestiona el índice FAISS para búsqueda semántica de documentos.
Usa el wrapper de LangChain para FAISS.
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from src.rag_pipeline.embeddings import embeddings_manager
from src.config.paths import VECTORSTORE_DIR

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """
    Gestor del vector store FAISS.
    
    Características:
    - Usa FAISS de LangChain para búsqueda eficiente
    - Integración con EmbeddingsManager
    - Persistencia en disco
    - Búsqueda por similitud con scores
    - Soporte para score threshold
    """
    
    def __init__(self, index_name: str = "faiss_index", embeddings_manager_instance=None):
        """
        Inicializa el vector store.
        
        Args:
            index_name: Nombre del índice (default: desde paths.py)
            embeddings_manager_instance: Instancia de EmbeddingsManager (opcional)
        """
        self.index_name = index_name
        self.embeddings_manager = embeddings_manager_instance or embeddings_manager
        self.vectorstore: Optional[FAISS] = None
        self.index_path = VECTORSTORE_DIR / index_name
        
        # Cargar configuración
        settings = self._load_settings()
        self.top_k = settings.get('top_k', 5)
        self.similarity_metric = settings.get('similarity_metric', 'cosine')
        
        logger.info(f"VectorStoreManager inicializado (índice: {index_name})")
    
    def _load_settings(self) -> Dict[str, Any]:
        """
        Carga configuración desde settings.yaml.
        
        Returns:
            Diccionario con configuración de FAISS
        """
        try:
            settings_path = Path(__file__).parent.parent / "config" / "settings.yaml"
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = yaml.safe_load(f)
                return settings.get('faiss', {})
        except Exception as e:
            logger.warning(f"Error cargando settings.yaml: {e}, usando valores por defecto")
            return {'top_k': 5, 'similarity_metric': 'cosine'}
    
    def create_index(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Crea índice FAISS a partir de documentos con embeddings.
        
        Los documentos deben tener la estructura:
        {'content': str, 'metadata': dict, 'embedding': List[float]}
        
        Args:
            documents: Lista de documentos con embeddings ya generados
            
        Returns:
            True si se creó exitosamente, False en caso contrario
        """
        if not documents:
            logger.warning("No hay documentos para indexar")
            return False
        
        try:
            logger.info(f"Creando índice FAISS con {len(documents)} documentos...")
            
            # Convertir documentos al formato de LangChain
            langchain_docs = []
            for doc in documents:
                content = doc.get('content', '')
                metadata = doc.get('metadata', {})
                langchain_docs.append(Document(page_content=content, metadata=metadata))
            
            # Crear índice FAISS usando embeddings del EmbeddingsManager
            self.vectorstore = FAISS.from_documents(
                documents=langchain_docs,
                embedding=self.embeddings_manager.embeddings
            )
            
            logger.info(f"Índice FAISS creado exitosamente con {len(documents)} documentos")
            return True
            
        except Exception as e:
            logger.error(f"Error creando índice FAISS: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def similarity_search(self, query: str, k: int = 5, 
                         score_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Búsqueda por similitud en el índice FAISS.
        
        Args:
            query: Texto de consulta
            k: Número de documentos a recuperar
            score_threshold: Umbral mínimo de similitud (None = no filtrar)
            
        Returns:
            Lista de documentos con formato: {'content': str, 'metadata': dict, 'score': float}
        """
        if self.vectorstore is None:
            logger.warning("No hay índice creado. Usa create_index() primero.")
            return []
        
        try:
            # Realizar búsqueda con FAISS
            # similarity_search_with_score retorna (Document, score)
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            
            # Convertir a formato estándar
            documents = []
            for doc, score in results:
                # FAISS usa distancia, convertir a similitud (1 - distancia para cosine)
                # Para embeddings normalizados, la distancia L2 puede convertirse a similitud
                similarity_score = float(1.0 - score) if score <= 1.0 else float(score)
                
                doc_dict = {
                    'content': doc.page_content,
                    'metadata': doc.metadata.copy(),
                    'score': similarity_score
                }
                
                # Filtrar por threshold si se especifica
                if score_threshold is None or similarity_score >= score_threshold:
                    documents.append(doc_dict)
            
            logger.info(f"Búsqueda completada: {len(documents)} documentos encontrados")
            return documents
            
        except Exception as e:
            logger.error(f"Error en búsqueda de similitud: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def save_index(self, index_path: Optional[str] = None) -> bool:
        """
        Guarda el índice FAISS en disco.
        
        Args:
            index_path: Ruta donde guardar (default: VECTORSTORE_DIR/index_name)
            
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        if self.vectorstore is None:
            logger.warning("No hay índice para guardar")
            return False
        
        try:
            save_path = Path(index_path) if index_path else self.index_path
            
            # Crear directorio si no existe
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Guardar índice FAISS
            self.vectorstore.save_local(str(save_path))
            
            logger.info(f"Índice guardado en: {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando índice: {e}")
            return False
    
    def load_index(self, index_path: Optional[str] = None) -> bool:
        """
        Carga un índice FAISS desde disco.
        
        Args:
            index_path: Ruta del índice (default: VECTORSTORE_DIR/index_name)
            
        Returns:
            True si se cargó exitosamente, False en caso contrario
        """
        try:
            load_path = Path(index_path) if index_path else self.index_path
            
            if not load_path.exists():
                logger.warning(f"Índice no encontrado en: {load_path}")
                return False
            
            # Cargar índice FAISS
            self.vectorstore = FAISS.load_local(
                str(load_path),
                self.embeddings_manager.embeddings,
                allow_dangerous_deserialization=True  # Necesario para cargar índices guardados
            )
            
            logger.info(f"Índice cargado desde: {load_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error cargando índice: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del índice.
        
        Returns:
            Diccionario con información del índice
        """
        if self.vectorstore is None:
            return {
                "status": "no_index",
                "index_name": self.index_name,
                "documents": 0
            }
        
        try:
            # Obtener número de documentos en el índice
            num_docs = self.vectorstore.index.ntotal if hasattr(self.vectorstore, 'index') else 0
            
            return {
                "status": "active",
                "index_name": self.index_name,
                "documents": num_docs,
                "index_path": str(self.index_path),
                "embedding_dimension": self.embeddings_manager.get_embedding_dimension(),
                "similarity_metric": self.similarity_metric
            }
        except Exception as e:
            logger.warning(f"Error obteniendo estadísticas: {e}")
            return {
                "status": "error",
                "index_name": self.index_name,
                "error": str(e)
            }
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Agrega documentos adicionales a un índice existente.
        
        Args:
            documents: Lista de documentos con embeddings
            
        Returns:
            True si se agregaron exitosamente
        """
        if self.vectorstore is None:
            logger.warning("No hay índice existente. Usa create_index() primero.")
            return False
        
        try:
            # Convertir a formato LangChain
            langchain_docs = []
            for doc in documents:
                content = doc.get('content', '')
                metadata = doc.get('metadata', {})
                langchain_docs.append(Document(page_content=content, metadata=metadata))
            
            # Agregar al índice existente
            self.vectorstore.add_documents(langchain_docs)
            
            logger.info(f"Agregados {len(documents)} documentos al índice")
            return True
            
        except Exception as e:
            logger.error(f"Error agregando documentos: {e}")
            return False


# Instancia global
vectorstore_manager = VectorStoreManager()
