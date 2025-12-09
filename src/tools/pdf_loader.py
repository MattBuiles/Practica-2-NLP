"""
Tool para cargar documentos PDF.
Implementación: Persona 2

Extrae texto y metadatos de archivos PDF usando pypdf.
"""
import logging
from typing import List, Dict, Any
from pathlib import Path
from pypdf import PdfReader


logger = logging.getLogger(__name__)


class PDFLoaderTool:
    """
    Herramienta para cargar documentos PDF.
    
    Características:
    - Extrae texto de todas las páginas
    - Extrae metadatos (número de páginas, título, autor si disponible)
    - Maneja errores de PDFs corruptos
    - Retorna formato estándar compatible con el pipeline
    """
    
    name = "pdf_loader"
    description = "Carga y extrae texto de archivos PDF"
    
    @staticmethod
    def load_pdf(file_path: str, max_file_size_mb: float = 50.0) -> List[Dict[str, Any]]:
        """
        Carga un PDF y extrae texto y metadatos.
        
        Args:
            file_path: Ruta al archivo PDF
            max_file_size_mb: Tamaño máximo del archivo en MB (default: 50)
            
        Returns:
            Lista de documentos con formato estándar:
            [
                {
                    'content': str,  # Texto extraído
                    'metadata': {
                        'source': str,      # Nombre del archivo
                        'page': int,        # Número de página
                        'file_path': str,   # Ruta completa
                        'total_pages': int, # Total de páginas
                        'title': str,       # Título del PDF (si disponible)
                        'author': str       # Autor del PDF (si disponible)
                    }
                },
                ...
            ]
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el archivo es demasiado grande o está corrupto
        """
        if PdfReader is None:
            raise ImportError("pypdf o PyPDF2 no están instalados. Instala con: pip install pypdf")
        
        file_path_obj = Path(file_path)
        
        # Validar que el archivo existe
        if not file_path_obj.exists():
            logger.error(f"Archivo PDF no encontrado: {file_path}")
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        # Validar tamaño del archivo
        file_size_mb = file_path_obj.stat().st_size / (1024 * 1024)
        if file_size_mb > max_file_size_mb:
            error_msg = f"Archivo demasiado grande: {file_size_mb:.2f} MB (máximo: {max_file_size_mb} MB)"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Cargando PDF: {file_path_obj.name} ({file_size_mb:.2f} MB)")
        
        documents = []
        
        try:
            # Leer PDF
            with open(file_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                
                # Extraer metadatos del PDF
                metadata = pdf_reader.metadata or {}
                pdf_title = metadata.get('/Title', '') or metadata.get('Title', '')
                pdf_author = metadata.get('/Author', '') or metadata.get('Author', '')
                total_pages = len(pdf_reader.pages)
                
                logger.info(f"PDF cargado: {total_pages} páginas, título: {pdf_title[:50] if pdf_title else 'N/A'}")
                
                # Extraer texto de cada página
                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    try:
                        text = page.extract_text()
                        
                        # Si la página está vacía, saltarla
                        if not text or len(text.strip()) < 10:
                            logger.debug(f"Página {page_num} vacía o con muy poco texto, omitiendo")
                            continue
                        
                        # Crear documento con formato estándar
                        doc = {
                            'content': text,
                            'metadata': {
                                'source': file_path_obj.name,
                                'page': page_num,
                                'file_path': str(file_path_obj.absolute()),
                                'total_pages': total_pages,
                                'title': pdf_title if pdf_title else None,
                                'author': pdf_author if pdf_author else None
                            }
                        }
                        
                        documents.append(doc)
                        logger.debug(f"Página {page_num}/{total_pages} extraída: {len(text)} caracteres")
                        
                    except Exception as e:
                        logger.warning(f"Error extrayendo página {page_num} de {file_path_obj.name}: {str(e)}")
                        # Continuar con la siguiente página
                        continue
                
                if not documents:
                    logger.warning(f"No se pudo extraer texto del PDF: {file_path_obj.name}")
                    raise ValueError(f"No se pudo extraer texto del PDF: {file_path_obj.name}")
                
                logger.info(f"PDF procesado exitosamente: {len(documents)} páginas con contenido")
                return documents
                
        except FileNotFoundError:
            raise
        except ValueError:
            raise
        except Exception as e:
            error_msg = f"Error procesando PDF {file_path_obj.name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e
    
    @staticmethod
    def load_multiple_pdfs(file_paths: List[str], max_file_size_mb: float = 50.0) -> List[Dict[str, Any]]:
        """
        Carga múltiples PDFs y retorna todos los documentos combinados.
        
        Args:
            file_paths: Lista de rutas a archivos PDF
            max_file_size_mb: Tamaño máximo por archivo en MB (default: 50)
            
        Returns:
            Lista combinada de todos los documentos de todos los PDFs
            
        Nota:
            Si un PDF falla, se registra el error pero se continúa con los demás.
        """
        all_documents = []
        successful = 0
        failed = 0
        
        logger.info(f"Cargando {len(file_paths)} archivos PDF...")
        
        for file_path in file_paths:
            try:
                documents = PDFLoaderTool.load_pdf(file_path, max_file_size_mb)
                all_documents.extend(documents)
                successful += 1
                logger.debug(f"✓ {Path(file_path).name}: {len(documents)} páginas")
            except Exception as e:
                failed += 1
                logger.error(f"✗ Error cargando {Path(file_path).name}: {str(e)}")
                # Continuar con el siguiente archivo
                continue
        
        logger.info(f"Carga completada: {successful} exitosos, {failed} fallidos, {len(all_documents)} páginas totales")
        
        return all_documents
