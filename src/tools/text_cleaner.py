"""
Tool para limpieza de texto.
Implementación: Persona 2

Normaliza y limpia texto extraído de documentos para mejorar la calidad
del procesamiento posterior (chunking, embeddings, etc.).
"""
import logging
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class TextCleanerTool:
    """
    Herramienta para limpieza y normalización de texto.
    
    Características:
    - Normalización de espacios en blanco
    - Remoción de caracteres de control
    - Normalización de saltos de línea
    - Limpieza agresiva opcional (URLs, emails, puntuación)
    - Filtrado por longitud mínima
    - Preservación de estructura básica
    """
    
    name = "text_cleaner"
    description = "Limpia y normaliza texto"
    
    # Patrones regex para limpieza agresiva
    URL_PATTERN = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )
    
    @staticmethod
    def clean_text(text: str, aggressive: bool = False, 
                   min_length: int = 50) -> Optional[str]:
        """
        Limpia y normaliza texto.
        
        Args:
            text: Texto a limpiar
            aggressive: Si aplicar limpieza agresiva (remover URLs, emails, etc.)
            min_length: Longitud mínima del texto después de limpiar (None = no filtrar)
            
        Returns:
            Texto limpio o None si es muy corto (según min_length)
        """
        if not text:
            return None
        
        # Paso 1: Normalizar saltos de línea
        # Convertir todos los tipos de saltos de línea a \n
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Paso 2: Remover caracteres de control (excepto \n y \t)
        # Mantener solo caracteres imprimibles, espacios, saltos de línea y tabs
        text = ''.join(char for char in text if char.isprintable() or char in ['\n', '\t'])
        
        # Paso 3: Limpieza agresiva (si se solicita)
        if aggressive:
            # Remover URLs
            text = TextCleanerTool.URL_PATTERN.sub('', text)
            
            # Remover emails
            text = TextCleanerTool.EMAIL_PATTERN.sub('', text)
            
            # Normalizar puntuación múltiple (ej: "!!!" -> ".", "¡¡¡" -> ".")
            # Nota: Los caracteres ¡ y ¿ son diferentes de ! y ?
            text = re.sub(r'[!¡]{2,}', '.', text)
            text = re.sub(r'[?¿]{2,}', '?', text)
            text = re.sub(r'[.]{4,}', '...', text)  # 4+ puntos -> ...
        
        # Paso 4: Normalizar espacios en blanco
        # Reemplazar múltiples espacios por uno solo
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Normalizar múltiples saltos de línea (máximo 2 consecutivos)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remover espacios al inicio y final de cada línea
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        text = '\n'.join(lines)
        
        # Paso 5: Remover espacios al inicio y final del texto completo
        text = text.strip()
        
        # Paso 6: Filtrar por longitud mínima
        if min_length and len(text) < min_length:
            logger.debug(f"Texto filtrado por longitud insuficiente: {len(text)} < {min_length}")
            return None
        
        return text if text else None
    
    @staticmethod
    def clean_documents(documents: List[Dict[str, Any]], 
                       aggressive: bool = False,
                       min_length: int = 50) -> List[Dict[str, Any]]:
        """
        Limpia una lista de documentos.
        
        Args:
            documents: Lista de documentos con formato {'content': str, 'metadata': dict}
            aggressive: Si aplicar limpieza agresiva
            min_length: Longitud mínima del contenido después de limpiar
            
        Returns:
            Lista de documentos limpios (se filtran los que quedan muy cortos)
        """
        cleaned_docs = []
        filtered_count = 0
        
        logger.info(f"Limpiando {len(documents)} documentos (aggressive={aggressive}, min_length={min_length})...")
        
        for doc in documents:
            original_content = doc.get('content', '')
            
            if not original_content:
                filtered_count += 1
                logger.debug(f"Documento sin contenido, omitiendo")
                continue
            
            cleaned_content = TextCleanerTool.clean_text(
                original_content, 
                aggressive=aggressive,
                min_length=min_length
            )
            
            if cleaned_content:
                # Crear nuevo documento con contenido limpio
                cleaned_doc = {
                    'content': cleaned_content,
                    'metadata': doc.get('metadata', {}).copy()
                }
                
                # Agregar información de limpieza a metadata
                if 'cleaning_info' not in cleaned_doc['metadata']:
                    cleaned_doc['metadata']['cleaning_info'] = {}
                
                cleaned_doc['metadata']['cleaning_info'] = {
                    'original_length': len(original_content),
                    'cleaned_length': len(cleaned_content),
                    'aggressive': aggressive,
                    'reduction_percent': round(
                        (1 - len(cleaned_content) / len(original_content)) * 100, 2
                    ) if original_content else 0
                }
                
                cleaned_docs.append(cleaned_doc)
            else:
                filtered_count += 1
                logger.debug(f"Documento filtrado por longitud insuficiente")
        
        logger.info(f"Limpieza completada: {len(cleaned_docs)} documentos válidos, {filtered_count} filtrados")
        
        return cleaned_docs
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        Normaliza espacios en blanco (método auxiliar).
        
        Args:
            text: Texto a normalizar
            
        Returns:
            Texto con espacios normalizados
        """
        # Reemplazar múltiples espacios por uno solo
        text = re.sub(r' +', ' ', text)
        # Reemplazar múltiples tabs por uno solo
        text = re.sub(r'\t+', '\t', text)
        # Normalizar saltos de línea múltiples
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    @staticmethod
    def remove_control_characters(text: str, preserve_newlines: bool = True) -> str:
        """
        Remueve caracteres de control (método auxiliar).
        
        Args:
            text: Texto a limpiar
            preserve_newlines: Si preservar saltos de línea y tabs
            
        Returns:
            Texto sin caracteres de control
        """
        if preserve_newlines:
            # Mantener solo caracteres imprimibles, espacios, \n y \t
            return ''.join(char for char in text if char.isprintable() or char in ['\n', '\t'])
        else:
            # Solo caracteres imprimibles y espacios
            return ''.join(char for char in text if char.isprintable() or char == ' ')
