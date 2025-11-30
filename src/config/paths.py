"""
Configuración de rutas del proyecto.
"""
import os
from pathlib import Path

# Ruta raíz del proyecto
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Rutas de datos
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"
SAMPLES_DIR = DATA_DIR / "samples"

# Rutas de logs
LOGS_DIR = PROJECT_ROOT / "logs"
TRACES_DIR = LOGS_DIR / "traces"
SYSTEM_LOGS_DIR = LOGS_DIR / "system_logs"

# Rutas de resultados
RESULTS_DIR = PROJECT_ROOT / "results"
CASOS_USO_DIR = RESULTS_DIR / "casos_de_uso"
RESPUESTAS_DIR = RESULTS_DIR / "respuestas"
CAPTURAS_DIR = RESULTS_DIR / "capturas"

# Rutas de experimentos
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"
NOTEBOOKS_DIR = EXPERIMENTS_DIR / "notebooks"
EVALUATIONS_DIR = EXPERIMENTS_DIR / "evaluations"

# Crear directorios si no existen
def create_directories():
    """Crea todos los directorios necesarios para el proyecto."""
    directories = [
        RAW_DATA_DIR, PROCESSED_DATA_DIR, VECTORSTORE_DIR, SAMPLES_DIR,
        TRACES_DIR, SYSTEM_LOGS_DIR,
        CASOS_USO_DIR, RESPUESTAS_DIR, CAPTURAS_DIR,
        NOTEBOOKS_DIR, EVALUATIONS_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# Nombres de archivos importantes
VECTORSTORE_INDEX = "faiss_index"
METADATA_FILE = "documents_metadata.json"
TRACE_LOG_FILE = "execution_trace.json"
