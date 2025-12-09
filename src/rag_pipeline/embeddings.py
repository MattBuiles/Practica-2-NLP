"""
Gestión de embeddings.
Implementación: Persona 2

Genera embeddings usando HuggingFaceEmbeddings con el modelo
sentence-transformers/all-MiniLM-L6-v2.
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml

from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


class EmbeddingsManager:
    """
    Gestor de embeddings.
    
    Características:
    - Usa HuggingFaceEmbeddings de LangChain
    - Modelo: sentence-transformers/all-MiniLM-L6-v2 (384 dimensiones)
    - Configuración desde settings.yaml
    - Soporte para generar embeddings de texto individual o batch
    - Normalización automática de embeddings
    """
    
    def __init__(self, model_name: Optional[str] = None, device: str = "cpu"):
        """
        Inicializa el gestor de embeddings.
        
        Args:
            model_name: Nombre del modelo (default: desde settings.yaml)
            device: Dispositivo a usar ('cpu' o 'cuda')
        """
        # Cargar configuración desde settings.yaml
        settings = self._load_settings()
        
        self.model_name = model_name or settings.get('model', 'sentence-transformers/all-MiniLM-L6-v2')
        self.device = device
        
        # Inicializar el modelo de embeddings
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.model_name,
                model_kwargs={'device': self.device},
                encode_kwargs={'normalize_embeddings': True}  # Normalizar para cosine similarity
            )
            logger.info(f"EmbeddingsManager inicializado con modelo: {self.model_name}")
            logger.info(f"Dispositivo: {self.device}, Dimensión: {self.get_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Error inicializando modelo de embeddings: {e}")
            raise
    
    def _load_settings(self) -> Dict[str, Any]:
        """
        Carga configuración desde settings.yaml.
        
        Returns:
            Diccionario con configuración de embeddings
        """
        try:
            settings_path = Path(__file__).parent.parent / "config" / "settings.yaml"
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = yaml.safe_load(f)
                return settings.get('embeddings', {})
        except Exception as e:
            logger.warning(f"Error cargando settings.yaml: {e}, usando valores por defecto")
            return {'model': 'sentence-transformers/all-MiniLM-L6-v2'}
    
    def get_embedding_dimension(self) -> int:
        """
        Retorna la dimensión de los embeddings.
        
        Returns:
            Dimensión del vector de embedding (384 para all-MiniLM-L6-v2)
        """
        # all-MiniLM-L6-v2 tiene 384 dimensiones
        if 'all-MiniLM-L6-v2' in self.model_name:
            return 384
        else:
            # Para otros modelos, intentar obtener la dimensión del modelo
            try:
                # Generar un embedding de prueba para obtener la dimensión
                test_embedding = self.embeddings.embed_query("test")
                return len(test_embedding)
            except Exception:
                logger.warning("No se pudo determinar la dimensión, usando 384 por defecto")
                return 384
    
    def embed_text(self, text: str) -> List[float]:
        """
        Genera embedding para un texto individual.
        
        Args:
            text: Texto a convertir en embedding
            
        Returns:
            Lista de floats representando el vector de embedding
        """
        if not text or not text.strip():
            logger.warning("Texto vacío proporcionado para embedding")
            return [0.0] * self.get_embedding_dimension()
        
        try:
            embedding = self.embeddings.embed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            raise
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Genera embeddings para múltiples textos (batch).
        
        Args:
            texts: Lista de textos a convertir en embeddings
            
        Returns:
            Lista de listas de floats, cada una representando un vector de embedding
        """
        if not texts:
            return []
        
        # Filtrar textos vacíos
        valid_texts = [text for text in texts if text and text.strip()]
        if not valid_texts:
            logger.warning("No hay textos válidos para generar embeddings")
            return []
        
        try:
            embeddings = self.embeddings.embed_documents(valid_texts)
            return embeddings
        except Exception as e:
            logger.error(f"Error generando embeddings en batch: {e}")
            raise
    
    def embed_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Genera embeddings para una lista de documentos.
        
        Los documentos deben tener la estructura: {'content': str, 'metadata': dict}
        
        Args:
            documents: Lista de documentos con 'content' y 'metadata'
            
        Returns:
            Lista de documentos con 'embedding' agregado a cada uno
        """
        if not documents:
            return []
        
        # Extraer textos
        texts = [doc.get('content', '') for doc in documents]
        
        # Generar embeddings
        embeddings = self.embed_texts(texts)
        
        # Agregar embeddings a los documentos
        result = []
        for doc, embedding in zip(documents, embeddings):
            doc_copy = doc.copy()
            doc_copy['embedding'] = embedding
            result.append(doc_copy)
        
        logger.info(f"Embeddings generados para {len(result)} documentos")
        return result


# Instancia global
embeddings_manager = EmbeddingsManager()
