"""
Tool para cargar documentos HTML.
Implementación: Persona 2

Extrae texto y metadatos de archivos HTML usando BeautifulSoup.
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import re
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class HTMLLoaderTool:
    """
    Herramienta para cargar documentos HTML.
    
    Características:
    - Extrae texto de etiquetas relevantes (<p>, <article>, <div>, etc.)
    - Remueve scripts, estilos y etiquetas no textuales
    - Extrae título de <title> o <h1>
    - Maneja encoding correctamente (UTF-8)
    - Retorna formato estándar compatible con el pipeline
    """
    
    name = "html_loader"
    description = "Carga y parsea archivos HTML"
    
    # Etiquetas de las que extraer texto
    TEXT_TAGS = ['p', 'article', 'div', 'section', 'main', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                 'li', 'td', 'th', 'span', 'blockquote', 'pre', 'code']
    
    # Etiquetas a remover completamente
    REMOVE_TAGS = ['script', 'style', 'noscript', 'meta', 'link', 'head', 'nav', 'footer', 
                   'header', 'aside', 'iframe', 'embed', 'object', 'canvas']
    
    @staticmethod
    def load_html(file_path: str, max_file_size_mb: float = 50.0) -> List[Dict[str, Any]]:
        """
        Carga un archivo HTML y extrae texto y metadatos.
        
        Args:
            file_path: Ruta al archivo HTML
            max_file_size_mb: Tamaño máximo del archivo en MB (default: 50)
            
        Returns:
            Lista de documentos con formato estándar:
            [
                {
                    'content': str,  # Texto extraído
                    'metadata': {
                        'source': str,      # Nombre del archivo
                        'file_path': str,   # Ruta completa
                        'title': str,       # Título del HTML (si disponible)
                        'section': str      # Sección del documento (si se divide)
                    }
                },
                ...
            ]
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el archivo es demasiado grande o está corrupto
        """
        if BeautifulSoup is None:
            raise ImportError("beautifulsoup4 no está instalado. Instala con: pip install beautifulsoup4 lxml")
        
        file_path_obj = Path(file_path)
        
        # Validar que el archivo existe
        if not file_path_obj.exists():
            logger.error(f"Archivo HTML no encontrado: {file_path}")
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        # Validar tamaño del archivo
        file_size_mb = file_path_obj.stat().st_size / (1024 * 1024)
        if file_size_mb > max_file_size_mb:
            error_msg = f"Archivo demasiado grande: {file_size_mb:.2f} MB (máximo: {max_file_size_mb} MB)"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Cargando HTML: {file_path_obj.name} ({file_size_mb:.2f} MB)")
        
        try:
            # Leer archivo con detección de encoding
            with open(file_path, 'rb') as file:
                raw_data = file.read()
            
            # Intentar detectar encoding
            encoding = HTMLLoaderTool._detect_encoding(raw_data)
            html_content = raw_data.decode(encoding, errors='replace')
            
            # Parsear con BeautifulSoup
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Extraer título
            html_title = HTMLLoaderTool._extract_title(soup)
            
            # Remover etiquetas no deseadas
            HTMLLoaderTool._remove_unwanted_tags(soup)
            
            # Extraer texto de etiquetas relevantes
            text_content = HTMLLoaderTool._extract_text(soup)
            
            if not text_content or len(text_content.strip()) < 10:
                logger.warning(f"No se pudo extraer texto significativo del HTML: {file_path_obj.name}")
                raise ValueError(f"No se pudo extraer texto del HTML: {file_path_obj.name}")
            
            # Dividir en secciones si es muy largo (opcional, para documentos grandes)
            # Por ahora, retornamos un solo documento
            doc = {
                'content': text_content,
                'metadata': {
                    'source': file_path_obj.name,
                    'file_path': str(file_path_obj.absolute()),
                    'title': html_title if html_title else None,
                    'section': 'main'  # Por defecto, todo el contenido
                }
            }
            
            logger.info(f"HTML procesado exitosamente: {len(text_content)} caracteres extraídos")
            return [doc]
            
        except FileNotFoundError:
            raise
        except ValueError:
            raise
        except Exception as e:
            error_msg = f"Error procesando HTML {file_path_obj.name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e
    
    @staticmethod
    def _detect_encoding(raw_data: bytes) -> str:
        """
        Detecta el encoding del archivo HTML.
        
        Args:
            raw_data: Contenido raw del archivo en bytes
            
        Returns:
            Nombre del encoding detectado
        """
        # Intentar detectar desde meta charset
        try:
            # Buscar charset en los primeros bytes
            head_content = raw_data[:5000].decode('utf-8', errors='ignore')
            charset_match = re.search(r'charset=["\']?([^"\'>\s]+)', head_content, re.IGNORECASE)
            if charset_match:
                encoding = charset_match.group(1).lower()
                # Normalizar nombres comunes
                encoding_map = {
                    'utf8': 'utf-8',
                    'iso-8859-1': 'latin-1',
                    'iso8859-1': 'latin-1'
                }
                encoding = encoding_map.get(encoding, encoding)
                logger.debug(f"Encoding detectado desde meta: {encoding}")
                return encoding
        except Exception:
            pass
        
        # Fallback: intentar UTF-8
        try:
            raw_data.decode('utf-8')
            logger.debug("Encoding: UTF-8 (fallback)")
            return 'utf-8'
        except UnicodeDecodeError:
            # Último recurso: latin-1 (acepta cualquier byte)
            logger.debug("Encoding: latin-1 (fallback)")
            return 'latin-1'
    
    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> Optional[str]:
        """
        Extrae el título del HTML desde <title> o <h1>.
        
        Args:
            soup: Objeto BeautifulSoup parseado
            
        Returns:
            Título extraído o None
        """
        # Intentar desde <title>
        title_tag = soup.find('title')
        if title_tag and title_tag.get_text(strip=True):
            title = title_tag.get_text(strip=True)
            logger.debug(f"Título extraído desde <title>: {title[:50]}")
            return title
        
        # Intentar desde <h1>
        h1_tag = soup.find('h1')
        if h1_tag and h1_tag.get_text(strip=True):
            title = h1_tag.get_text(strip=True)
            logger.debug(f"Título extraído desde <h1>: {title[:50]}")
            return title
        
        # Intentar desde meta og:title
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            title = meta_title.get('content').strip()
            logger.debug(f"Título extraído desde og:title: {title[:50]}")
            return title
        
        return None
    
    @staticmethod
    def _remove_unwanted_tags(soup: BeautifulSoup):
        """
        Remueve etiquetas no deseadas del HTML.
        
        Args:
            soup: Objeto BeautifulSoup (se modifica in-place)
        """
        for tag_name in HTMLLoaderTool.REMOVE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()  # Remover completamente
    
    @staticmethod
    def _extract_text(soup: BeautifulSoup) -> str:
        """
        Extrae texto de las etiquetas relevantes.
        
        Args:
            soup: Objeto BeautifulSoup parseado
            
        Returns:
            Texto extraído y limpiado
        """
        # Buscar el contenido principal
        # Intentar encontrar <main>, <article>, o <body>
        content_containers = soup.find_all(['main', 'article', 'body'])
        
        if content_containers:
            # Usar el primer contenedor principal
            container = content_containers[0]
        else:
            # Usar todo el documento
            container = soup
        
        # Extraer texto de etiquetas relevantes
        text_parts = []
        
        for tag in container.find_all(HTMLLoaderTool.TEXT_TAGS):
            text = tag.get_text(separator=' ', strip=True)
            if text and len(text) > 10:  # Filtrar textos muy cortos
                text_parts.append(text)
        
        # Si no se encontró texto en etiquetas específicas, extraer todo
        if not text_parts:
            text = container.get_text(separator=' ', strip=True)
            text_parts.append(text)
        
        # Unir y limpiar
        full_text = ' '.join(text_parts)
        
        # Limpiar espacios múltiples
        full_text = re.sub(r'\s+', ' ', full_text)
        full_text = full_text.strip()
        
        return full_text
    
    @staticmethod
    def load_multiple_htmls(file_paths: List[str], max_file_size_mb: float = 50.0) -> List[Dict[str, Any]]:
        """
        Carga múltiples archivos HTML y retorna todos los documentos combinados.
        
        Args:
            file_paths: Lista de rutas a archivos HTML
            max_file_size_mb: Tamaño máximo por archivo en MB (default: 50)
            
        Returns:
            Lista combinada de todos los documentos de todos los HTMLs
            
        Nota:
            Si un HTML falla, se registra el error pero se continúa con los demás.
        """
        all_documents = []
        successful = 0
        failed = 0
        
        logger.info(f"Cargando {len(file_paths)} archivos HTML...")
        
        for file_path in file_paths:
            try:
                documents = HTMLLoaderTool.load_html(file_path, max_file_size_mb)
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
