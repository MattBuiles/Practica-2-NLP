"""
Chunking de documentos.
Implementación: Persona 2

Divide documentos en chunks usando RecursiveCharacterTextSplitter de LangChain
con configuración desde settings.yaml.
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class DocumentChunker:
    """
    Gestor de chunking de documentos.
    
    Características:
    - Usa RecursiveCharacterTextSplitter de LangChain
    - Configuración desde settings.yaml (chunk_size, chunk_overlap)
    - Separadores jerárquicos para mantener contexto
    - Agrega metadatos a cada chunk (índice, total, fuente)
    """
    
    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        """
        Inicializa el chunker.
        
        Args:
            chunk_size: Tamaño de chunks en caracteres (default: desde settings.yaml)
            chunk_overlap: Overlap entre chunks en caracteres (default: desde settings.yaml)
        """
        # Cargar configuración desde settings.yaml
        settings = self._load_settings()
        
        self.chunk_size = chunk_size or settings.get('chunk_size', 1000)
        self.chunk_overlap = chunk_overlap or settings.get('chunk_overlap', 200)
        
        # Separadores jerárquicos (orden de preferencia)
        self.separators = ["\n\n", "\n", ". ", " ", ""]
        
        # Inicializar el splitter de LangChain
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len,
            is_separator_regex=False
        )
        
        logger.info(f"DocumentChunker inicializado: chunk_size={self.chunk_size}, overlap={self.chunk_overlap}")
    
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
            return {'chunk_size': 1000, 'chunk_overlap': 200}
    
    def chunk_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Divide documentos en chunks con overlap.
        
        Args:
            documents: Lista de documentos con formato:
                [
                    {
                        'content': str,
                        'metadata': {
                            'source': str,
                            'file_path': str,
                            ...
                        }
                    },
                    ...
                ]
        
        Returns:
            Lista de chunks con formato:
                [
                    {
                        'content': str,  # Contenido del chunk
                        'metadata': {
                            'source': str,        # Nombre del archivo original
                            'file_path': str,     # Ruta completa
                            'chunk_index': int,   # Índice del chunk (0-based)
                            'total_chunks': int,  # Total de chunks del documento
                            ... (otros metadatos del documento original)
                        }
                    },
                    ...
                ]
        """
        if not documents:
            logger.warning("Lista de documentos vacía, retornando lista vacía")
            return []
        
        all_chunks = []
        
        logger.info(f"Chunking {len(documents)} documentos...")
        
        for doc_idx, doc in enumerate(documents):
            content = doc.get('content', '')
            metadata = doc.get('metadata', {}).copy()
            
            if not content or len(content.strip()) < 10:
                logger.debug(f"Documento {doc_idx} sin contenido suficiente, omitiendo")
                continue
            
            # Obtener información de fuente
            source = metadata.get('source', f'document_{doc_idx}')
            file_path = metadata.get('file_path', '')
            
            try:
                # Dividir el documento en chunks
                chunks = self.text_splitter.split_text(content)
                
                if not chunks:
                    logger.warning(f"No se generaron chunks para documento: {source}")
                    continue
                
                logger.debug(f"Documento '{source}': {len(chunks)} chunks generados")
                
                # Crear chunks con metadatos
                for chunk_idx, chunk_text in enumerate(chunks):
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        'chunk_index': chunk_idx,
                        'total_chunks': len(chunks),
                        'source': source,
                        'file_path': file_path
                    })
                    
                    chunk = {
                        'content': chunk_text,
                        'metadata': chunk_metadata
                    }
                    
                    all_chunks.append(chunk)
                
            except Exception as e:
                logger.error(f"Error chunking documento '{source}': {str(e)}", exc_info=True)
                # Continuar con el siguiente documento
                continue
        
        logger.info(f"Chunking completado: {len(all_chunks)} chunks generados de {len(documents)} documentos")
        
        return all_chunks
    
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Divide un texto en chunks (método auxiliar).
        
        Args:
            text: Texto a dividir
            metadata: Metadatos opcionales para agregar a los chunks
            
        Returns:
            Lista de chunks con formato estándar
        """
        if not text or len(text.strip()) < 10:
            logger.warning("Texto muy corto para chunking")
            return []
        
        try:
            chunks = self.text_splitter.split_text(text)
            
            result = []
            for chunk_idx, chunk_text in enumerate(chunks):
                chunk_metadata = (metadata or {}).copy()
                chunk_metadata.update({
                    'chunk_index': chunk_idx,
                    'total_chunks': len(chunks)
                })
                
                result.append({
                    'content': chunk_text,
                    'metadata': chunk_metadata
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error chunking texto: {str(e)}", exc_info=True)
            return []


# Instancia global
document_chunker = DocumentChunker()
