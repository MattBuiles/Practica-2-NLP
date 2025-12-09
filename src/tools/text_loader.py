"""
Tool para cargar documentos de texto plano.
Implementación: Persona 2

Extrae texto de archivos TXT con detección automática de encoding.
"""
import logging
from typing import List, Dict, Any
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class TextLoaderTool:
    """
    Herramienta para cargar documentos de texto plano.
    
    Características:
    - Detección automática de encoding (UTF-8, Latin-1, etc.)
    - División en párrafos si es necesario
    - Mantiene estructura básica del texto
    - Retorna formato estándar compatible con el pipeline
    """
    
    name = "text_loader"
    description = "Carga y procesa archivos de texto plano"
    
    # Encodings a probar en orden de preferencia
    ENCODINGS_TO_TRY = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
    
    @staticmethod
    def load_text(file_path: str, max_file_size_mb: float = 50.0, 
                  split_paragraphs: bool = True) -> List[Dict[str, Any]]:
        """
        Carga un archivo de texto plano y extrae su contenido.
        
        Args:
            file_path: Ruta al archivo TXT
            max_file_size_mb: Tamaño máximo del archivo en MB (default: 50)
            split_paragraphs: Si dividir el texto en párrafos (default: True)
            
        Returns:
            Lista de documentos con formato estándar:
            [
                {
                    'content': str,  # Texto extraído (párrafo o documento completo)
                    'metadata': {
                        'source': str,      # Nombre del archivo
                        'file_path': str,   # Ruta completa
                        'paragraph': int    # Número de párrafo (si split_paragraphs=True)
                    }
                },
                ...
            ]
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el archivo es demasiado grande o no se puede leer
        """
        file_path_obj = Path(file_path)
        
        # Validar que el archivo existe
        if not file_path_obj.exists():
            logger.error(f"Archivo TXT no encontrado: {file_path}")
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        # Validar tamaño del archivo
        file_size_mb = file_path_obj.stat().st_size / (1024 * 1024)
        if file_size_mb > max_file_size_mb:
            error_msg = f"Archivo demasiado grande: {file_size_mb:.2f} MB (máximo: {max_file_size_mb} MB)"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Cargando TXT: {file_path_obj.name} ({file_size_mb:.2f} MB)")
        
        try:
            # Leer archivo con detección de encoding
            encoding = TextLoaderTool._detect_encoding(file_path_obj)
            logger.debug(f"Encoding detectado: {encoding}")
            
            with open(file_path_obj, 'r', encoding=encoding, errors='replace') as file:
                content = file.read()
            
            if not content or len(content.strip()) < 10:
                logger.warning(f"Archivo TXT vacío o con muy poco contenido: {file_path_obj.name}")
                raise ValueError(f"Archivo vacío o con contenido insuficiente: {file_path_obj.name}")
            
            # Dividir en párrafos si se solicita
            if split_paragraphs:
                paragraphs = TextLoaderTool._split_into_paragraphs(content)
                documents = []
                
                for para_num, paragraph in enumerate(paragraphs, start=1):
                    if len(paragraph.strip()) >= 10:  # Filtrar párrafos muy cortos
                        doc = {
                            'content': paragraph.strip(),
                            'metadata': {
                                'source': file_path_obj.name,
                                'file_path': str(file_path_obj.absolute()),
                                'paragraph': para_num,
                                'total_paragraphs': len(paragraphs)
                            }
                        }
                        documents.append(doc)
                
                if not documents:
                    logger.warning(f"No se pudieron extraer párrafos válidos de: {file_path_obj.name}")
                    raise ValueError(f"No se pudo extraer contenido del archivo: {file_path_obj.name}")
                
                logger.info(f"TXT procesado exitosamente: {len(documents)} párrafos extraídos")
                return documents
            else:
                # Retornar documento completo
                doc = {
                    'content': content.strip(),
                    'metadata': {
                        'source': file_path_obj.name,
                        'file_path': str(file_path_obj.absolute()),
                        'paragraph': None
                    }
                }
                logger.info(f"TXT procesado exitosamente: {len(content)} caracteres")
                return [doc]
            
        except FileNotFoundError:
            raise
        except ValueError:
            raise
        except UnicodeDecodeError as e:
            error_msg = f"Error de encoding al leer {file_path_obj.name}: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
        except Exception as e:
            error_msg = f"Error procesando TXT {file_path_obj.name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e
    
    @staticmethod
    def _detect_encoding(file_path: Path) -> str:
        """
        Detecta el encoding del archivo de texto.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Nombre del encoding detectado
        """
        # Leer una muestra del archivo en modo binario
        with open(file_path, 'rb') as file:
            sample = file.read(8192)  # Leer primeros 8KB
        
        # Probar encodings en orden de preferencia
        for encoding in TextLoaderTool.ENCODINGS_TO_TRY:
            try:
                sample.decode(encoding)
                logger.debug(f"Encoding detectado: {encoding}")
                return encoding
            except (UnicodeDecodeError, LookupError):
                continue
        
        # Si ninguno funciona, usar UTF-8 con reemplazo de errores
        logger.warning(f"No se pudo detectar encoding para {file_path.name}, usando UTF-8 con reemplazo")
        return 'utf-8'
    
    @staticmethod
    def _split_into_paragraphs(text: str) -> List[str]:
        """
        Divide el texto en párrafos.
        
        Un párrafo se define como:
        - Bloques de texto separados por dos o más saltos de línea
        - O bloques de texto separados por un salto de línea seguido de espacio en blanco
        
        Args:
            text: Texto completo a dividir
            
        Returns:
            Lista de párrafos
        """
        # Normalizar saltos de línea
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Dividir por párrafos (dos o más saltos de línea)
        # También considerar un salto de línea seguido de espacio como separador
        paragraphs = re.split(r'\n\s*\n+', text)
        
        # Limpiar párrafos
        cleaned_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            # Remover saltos de línea internos y reemplazar por espacios
            para = re.sub(r'\n+', ' ', para)
            # Limpiar espacios múltiples
            para = re.sub(r'\s+', ' ', para)
            para = para.strip()
            
            if para and len(para) >= 10:  # Filtrar párrafos muy cortos
                cleaned_paragraphs.append(para)
        
        # Si no se encontraron párrafos claros, dividir por saltos de línea simples
        if not cleaned_paragraphs:
            lines = text.split('\n')
            current_para = []
            
            for line in lines:
                line = line.strip()
                if line:
                    current_para.append(line)
                else:
                    if current_para:
                        para_text = ' '.join(current_para)
                        if len(para_text) >= 10:
                            cleaned_paragraphs.append(para_text)
                        current_para = []
            
            # Agregar último párrafo si existe
            if current_para:
                para_text = ' '.join(current_para)
                if len(para_text) >= 10:
                    cleaned_paragraphs.append(para_text)
        
        # Si aún no hay párrafos, retornar el texto completo como un párrafo
        if not cleaned_paragraphs:
            cleaned_text = re.sub(r'\s+', ' ', text.strip())
            if cleaned_text:
                cleaned_paragraphs.append(cleaned_text)
        
        return cleaned_paragraphs
    
    @staticmethod
    def load_multiple_texts(file_paths: List[str], max_file_size_mb: float = 50.0,
                            split_paragraphs: bool = True) -> List[Dict[str, Any]]:
        """
        Carga múltiples archivos de texto y retorna todos los documentos combinados.
        
        Args:
            file_paths: Lista de rutas a archivos TXT
            max_file_size_mb: Tamaño máximo por archivo en MB (default: 50)
            split_paragraphs: Si dividir el texto en párrafos (default: True)
            
        Returns:
            Lista combinada de todos los documentos de todos los archivos TXT
            
        Nota:
            Si un archivo falla, se registra el error pero se continúa con los demás.
        """
        all_documents = []
        successful = 0
        failed = 0
        
        logger.info(f"Cargando {len(file_paths)} archivos TXT...")
        
        for file_path in file_paths:
            try:
                documents = TextLoaderTool.load_text(file_path, max_file_size_mb, split_paragraphs)
                all_documents.extend(documents)
                successful += 1
                logger.debug(f"✓ {Path(file_path).name}: {len(documents)} documento(s)")
            except Exception as e:
                failed += 1
                logger.error(f"✗ Error cargando {Path(file_path).name}: {str(e)}")
                # Continuar con el siguiente archivo
                continue
        
        logger.info(f"Carga completada: {successful} exitosos, {failed} fallidos, {len(all_documents)} documentos totales")
        
        return all_documents

