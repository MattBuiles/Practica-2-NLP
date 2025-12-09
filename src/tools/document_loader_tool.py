"""
Document Loader Tool - LangChain Tool para cargar documentos de múltiples formatos.

Esta herramienta permite a los agentes cargar documentos PDF, HTML y TXT
de forma autónoma según las necesidades del proceso de indexación.
"""
import logging
from typing import List, Dict, Any
from pathlib import Path
from langchain_core.tools import tool

from src.tools.pdf_loader import PDFLoaderTool
from src.tools.html_loader import HTMLLoaderTool
from src.tools.text_loader import TextLoaderTool

logger = logging.getLogger(__name__)


@tool
def load_document(file_path: str) -> Dict[str, Any]:
    """
    Carga un documento individual (PDF, HTML o TXT) y lo convierte en formato estructurado.
    
    **¿Cuándo usar esta herramienta?**
    - Cuando necesitas cargar un archivo específico por su ruta
    - Cuando el tipo de archivo se determina automáticamente por su extensión
    - Para agregar documentos individuales al pipeline de indexación
    
    **Casos de uso:**
    - "Cargar el archivo X.pdf para indexación"
    - "Necesito procesar el documento Y.html"
    - "Agregar un nuevo archivo al índice"
    
    Args:
        file_path: Ruta completa del archivo a cargar
        
    Returns:
        Dict con:
        - status: "success" o "error"
        - documents: Lista de documentos cargados (cada uno con content y metadata)
        - file_type: Tipo detectado ("pdf", "html", "txt")
        - document_count: Cantidad de documentos generados
        - error: Mensaje de error (si aplica)
        
    Example:
        >>> result = load_document("data/raw/articulo.pdf")
        >>> print(result['status'])
        'success'
        >>> print(result['document_count'])
        5
    """
    try:
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            logger.warning(f"Archivo no existe: {file_path}")
            return {
                "status": "error",
                "error": f"Archivo no encontrado: {file_path}",
                "documents": [],
                "document_count": 0
            }
        
        file_ext = file_path_obj.suffix.lower()
        
        # Determinar tipo y cargar
        if file_ext == '.pdf':
            documents = PDFLoaderTool.load_pdf(str(file_path_obj))
            file_type = "pdf"
        elif file_ext in ['.html', '.htm']:
            documents = HTMLLoaderTool.load_html(str(file_path_obj))
            file_type = "html"
        elif file_ext == '.txt':
            documents = TextLoaderTool.load_text(str(file_path_obj))
            file_type = "txt"
        else:
            logger.warning(f"Tipo de archivo no soportado: {file_ext}")
            return {
                "status": "error",
                "error": f"Tipo de archivo no soportado: {file_ext}",
                "documents": [],
                "document_count": 0
            }
        
        logger.info(f"Cargado {file_path_obj.name}: {len(documents)} documentos")
        
        return {
            "status": "success",
            "documents": documents,
            "file_type": file_type,
            "document_count": len(documents),
            "file_name": file_path_obj.name
        }
        
    except Exception as e:
        logger.error(f"Error cargando documento {file_path}: {e}")
        return {
            "status": "error",
            "error": str(e),
            "documents": [],
            "document_count": 0
        }


@tool
def scan_directory_for_documents(directory_path: str, file_types: str = "pdf,html,txt") -> Dict[str, Any]:
    """
    Escanea un directorio y cuenta documentos por tipo sin cargarlos.
    
    **¿Cuándo usar esta herramienta?**
    - ANTES de cargar documentos, para saber qué hay disponible
    - Para validar que existen documentos antes de indexar
    - Para planificar el proceso de indexación basado en cantidad
    - Cuando necesitas estadísticas rápidas del directorio
    
    **Casos de uso:**
    - "¿Qué documentos hay disponibles para indexar?"
    - "Necesito saber cuántos PDFs hay antes de procesar"
    - "Verificar si el directorio tiene documentos"
    
    Args:
        directory_path: Ruta del directorio a escanear
        file_types: Tipos separados por coma (default: "pdf,html,txt")
        
    Returns:
        Dict con:
        - status: "success" o "error"
        - total_files: Total de archivos encontrados
        - files_by_type: Dict con conteo por tipo {"pdf": 10, "html": 5, ...}
        - file_list: Lista de rutas de archivos encontrados
        - directory: Directorio escaneado
        
    Example:
        >>> result = scan_directory_for_documents("data/raw")
        >>> print(f"Total: {result['total_files']}")
        Total: 125
        >>> print(result['files_by_type'])
        {'pdf': 80, 'html': 30, 'txt': 15}
    """
    try:
        dir_path = Path(directory_path)
        
        if not dir_path.exists():
            logger.error(f"Directorio no existe: {directory_path}")
            return {
                "status": "error",
                "error": f"Directorio no encontrado: {directory_path}",
                "total_files": 0,
                "files_by_type": {}
            }
        
        if not dir_path.is_dir():
            logger.error(f"La ruta no es un directorio: {directory_path}")
            return {
                "status": "error",
                "error": f"No es un directorio: {directory_path}",
                "total_files": 0,
                "files_by_type": {}
            }
        
        # Parsear tipos de archivo
        types = [t.strip() for t in file_types.split(',')]
        
        # Escanear por tipo
        files_by_type = {}
        all_files = []
        
        for file_type in types:
            if file_type == 'pdf':
                files = list(dir_path.glob("**/*.pdf"))
            elif file_type == 'html':
                files = list(dir_path.glob("**/*.html")) + list(dir_path.glob("**/*.htm"))
            elif file_type == 'txt':
                files = list(dir_path.glob("**/*.txt"))
            else:
                logger.warning(f"Tipo de archivo desconocido: {file_type}")
                continue
            
            files_by_type[file_type] = len(files)
            all_files.extend([str(f) for f in files])
        
        total = sum(files_by_type.values())
        
        logger.info(f"Escaneado {directory_path}: {total} archivos encontrados")
        
        return {
            "status": "success",
            "total_files": total,
            "files_by_type": files_by_type,
            "file_list": all_files,
            "directory": directory_path
        }
        
    except Exception as e:
        logger.error(f"Error escaneando directorio {directory_path}: {e}")
        return {
            "status": "error",
            "error": str(e),
            "total_files": 0,
            "files_by_type": {}
        }


@tool
def load_documents_batch(file_paths: List[str]) -> Dict[str, Any]:
    """
    Carga múltiples documentos en lote de forma eficiente.
    
    **¿Cuándo usar esta herramienta?**
    - Cuando tienes una lista específica de archivos para cargar
    - Para cargar documentos seleccionados del escaneo previo
    - Cuando necesitas cargar documentos de forma paralela/eficiente
    - Para reintentar carga de archivos fallidos
    
    **Casos de uso:**
    - "Cargar estos 10 archivos específicos"
    - "Procesar la lista de archivos que el usuario seleccionó"
    - "Cargar solo los PDFs nuevos"
    
    Args:
        file_paths: Lista de rutas de archivos a cargar
        
    Returns:
        Dict con:
        - status: "success", "partial", o "error"
        - total_documents: Total de documentos generados
        - documents: Lista de todos los documentos cargados
        - files_processed: Cantidad de archivos procesados exitosamente
        - files_failed: Cantidad de archivos fallidos
        - failed_files: Lista de archivos que fallaron
        - by_type: Estadísticas por tipo de archivo
        
    Example:
        >>> files = ["doc1.pdf", "doc2.html", "doc3.txt"]
        >>> result = load_documents_batch(files)
        >>> print(f"Procesados: {result['files_processed']}")
        Procesados: 3
        >>> print(f"Documentos: {result['total_documents']}")
        Documentos: 15
    """
    try:
        if not file_paths:
            return {
                "status": "error",
                "error": "No se proporcionaron archivos",
                "total_documents": 0,
                "documents": []
            }
        
        all_documents = []
        files_processed = 0
        files_failed = 0
        failed_files = []
        by_type = {"pdf": 0, "html": 0, "txt": 0}
        
        for file_path in file_paths:
            result = load_document.invoke({"file_path": file_path})
            
            if result["status"] == "success":
                all_documents.extend(result["documents"])
                files_processed += 1
                file_type = result["file_type"]
                by_type[file_type] = by_type.get(file_type, 0) + result["document_count"]
            else:
                files_failed += 1
                failed_files.append({
                    "file": file_path,
                    "error": result.get("error", "Unknown error")
                })
                logger.warning(f"Falló carga de {file_path}: {result.get('error')}")
        
        # Determinar status global
        if files_failed == 0:
            status = "success"
        elif files_processed == 0:
            status = "error"
        else:
            status = "partial"
        
        logger.info(f"Batch completado: {files_processed}/{len(file_paths)} archivos OK")
        
        return {
            "status": status,
            "total_documents": len(all_documents),
            "documents": all_documents,
            "files_processed": files_processed,
            "files_failed": files_failed,
            "failed_files": failed_files,
            "by_type": by_type
        }
        
    except Exception as e:
        logger.error(f"Error en carga batch: {e}")
        return {
            "status": "error",
            "error": str(e),
            "total_documents": 0,
            "documents": []
        }
