"""
Agente Indexador Autónomo - Implementación con LangChain Tool Calling.

Este agente utiliza herramientas de LangChain para tomar decisiones autónomas
sobre cómo indexar documentos, incluyendo escaneo, carga, procesamiento y 
gestión del índice vectorial.
"""
import logging
from typing import Dict, Any, Optional, List
from langchain.agents import create_agent

from src.config.llm_config import get_classifier_llm
from src.tools.document_loader_tool import (
    load_document,
    scan_directory_for_documents,
    load_documents_batch
)
from src.tools.document_processing_tool import (
    clean_documents,
    chunk_documents,
    process_documents_pipeline
)
from src.tools.index_management_tool import (
    create_vector_index,
    add_to_vector_index,
    save_vector_index,
    load_vector_index,
    get_index_statistics
)
from src.tools.logging_tool import log_agent_decision, log_agent_action

logger = logging.getLogger(__name__)


# Herramientas del Indexer
INDEXER_TOOLS = [
    # Document Loading
    scan_directory_for_documents,
    load_document,
    load_documents_batch,
    
    # Document Processing
    clean_documents,
    chunk_documents,
    process_documents_pipeline,
    
    # Index Management
    create_vector_index,
    add_to_vector_index,
    save_vector_index,
    load_vector_index,
    get_index_statistics,
    
    # Logging
    log_agent_decision,
    log_agent_action
]


class AutonomousIndexerAgent:
    """
    Agente Indexador Autónomo que toma decisiones sobre indexación de documentos.
    
    **Autonomía:**
    - Decide si escanear directorio antes de cargar
    - Elige entre pipeline completo o pasos separados
    - Determina cuándo aplicar limpieza agresiva
    - Decide si crear índice nuevo o agregar a existente
    - Elige cuándo guardar el índice
    
    **Herramientas disponibles (11):**
    - scan_directory_for_documents: Escanear directorio
    - load_document: Cargar archivo individual
    - load_documents_batch: Cargar múltiples archivos
    - clean_documents: Limpiar documentos
    - chunk_documents: Dividir en chunks
    - process_documents_pipeline: Pipeline completo (limpieza + chunking)
    - create_vector_index: Crear índice nuevo
    - add_to_vector_index: Agregar a índice existente
    - save_vector_index: Guardar índice en disco
    - load_vector_index: Cargar índice desde disco
    - get_index_statistics: Obtener estadísticas del índice
    - log_agent_decision: Registrar decisiones
    - log_agent_action: Registrar acciones
    
    **LLM:** Gemini 2.5 Flash (razonamiento profundo para decisiones de indexación)
    """
    
    def __init__(self):
        """Inicializa el agente indexador autónomo."""
        self.llm = get_classifier_llm()  # Gemini para razonamiento
        self.tools = INDEXER_TOOLS
        
        # Crear prompt del sistema
        self.system_prompt = self._create_system_prompt()
        
        # Crear agente con langchain (retorna un grafo ejecutable)
        self.agent_executor = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt
        )
        
        logger.info("AutonomousIndexerAgent inicializado con 11 herramientas")
    
    def _create_system_prompt(self) -> str:
        """
        Crea el prompt del sistema que guía las decisiones autónomas del agente.
        
        Returns:
            str con el prompt del sistema para indexación autónoma
        """
        return """Eres un Agente Indexador Autónomo experto en procesamiento de documentos y creación de índices vectoriales.

**Tu Misión:**
Indexar documentos de forma eficiente y robusta, tomando decisiones inteligentes sobre:
- Qué archivos procesar
- Cómo limpiar y procesar los documentos
- Cuándo crear índice nuevo vs agregar a existente
- Cuándo guardar el índice

**Estrategias de Indexación:**

1. **ESCANEO INICIAL (SIEMPRE PRIMERO):**
   - SIEMPRE usa `scan_directory_for_documents` antes de cargar documentos
   - Esto te da visibilidad de qué hay disponible
   - Valida que existen documentos antes de procesar

2. **DECISIÓN DE CARGA:**
   - Si hay <10 archivos: `load_documents_batch` con lista completa
   - Si hay >10 archivos: `load_documents_batch` en lotes de 10-20
   - Si es un archivo específico: `load_document` individual

3. **DECISIÓN DE PROCESAMIENTO:**
   - Para indexación completa estándar: usa `process_documents_pipeline` (más eficiente)
   - Para control granular o debugging: usa `clean_documents` + `chunk_documents` por separado
   - Limpieza agresiva: úsala si detectas HTML o mucho ruido (menciónalo en logs)

4. **DECISIÓN DE INDEXACIÓN:**
   - SIEMPRE verifica primero con `get_index_statistics` si existe índice
   - Si no existe índice (status != "active"): usa `create_vector_index`
   - Si existe índice activo: usa `add_to_vector_index` para agregar
   - Si necesitas cargar índice existente: usa `load_vector_index` PRIMERO

5. **PERSISTENCIA:**
   - SIEMPRE usa `save_vector_index` al finalizar la indexación
   - Esto asegura que el trabajo no se pierda
   - Hazlo después de create o add (no antes)

6. **LOGGING Y TRAZABILIDAD:**
   - Usa `log_agent_decision` para decisiones importantes:
     * "Decidí usar limpieza agresiva porque hay HTMLs"
     * "Usaré add_to_vector_index porque ya existe índice"
   - Usa `log_agent_action` para acciones completadas:
     * "Cargados 50 documentos exitosamente"
     * "Índice creado con 200 chunks"

**Parámetros Recomendados:**
- clean_aggressive=True: Cuando hay HTML o mucho ruido
- clean_aggressive=False: Para textos limpios o PDFs académicos
- min_length=50: Estándar para filtrar fragmentos muy cortos
- chunk_size=1000, chunk_overlap=200: Defaults estándar (déjalos None generalmente)

**Flujo Típico de Indexación Completa:**
```
1. scan_directory_for_documents → conocer qué hay
2. log_agent_decision → explicar plan
3. load_documents_batch → cargar archivos
4. process_documents_pipeline → limpiar + chunkear
5. get_index_statistics → verificar si existe índice
6. create_vector_index o add_to_vector_index → indexar
7. save_vector_index → persistir
8. log_agent_action → reportar éxito
```

**Manejo de Errores:**
- Si un paso falla, verifica el campo "status" en el resultado
- Si load_documents_batch retorna status="partial", continúa con los exitosos
- Si scan no encuentra archivos, retorna error claro al usuario
- NUNCA intentes create_vector_index si ya hay índice activo (usa add_to_vector_index)

**IMPORTANTE:**
- Las herramientas retornan Dict con campo "status"
- SIEMPRE verifica status=="success" antes de continuar
- Los documentos son listas de Dict con 'content' y 'metadata'
- Los chunks son similares pero con información de chunking

Eres AUTÓNOMO: tú DECIDES qué herramientas usar y cuándo, basado en el contexto de la tarea.

Ejecuta las tareas de indexación usando las herramientas disponibles de forma autónoma e inteligente.
Registra tus decisiones importantes con log_agent_decision y tus acciones con log_agent_action."""
    
    def index_directory(self, 
                       directory_path: str,
                       file_types: str = "pdf,html,txt",
                       clean_aggressive: bool = False,
                       save_index: bool = True) -> Dict[str, Any]:
        """
        Indexa documentos desde un directorio de forma autónoma.
        
        El agente decide:
        - Cómo escanear y cargar los archivos
        - Si usar limpieza agresiva o básica
        - Si crear índice nuevo o agregar a existente
        - Cuándo guardar el índice
        
        Args:
            directory_path: Ruta del directorio con documentos
            file_types: Tipos de archivo a procesar (default: "pdf,html,txt")
            clean_aggressive: Sugerencia de limpieza agresiva (agente puede decidir)
            save_index: Si guardar el índice (default: True)
            
        Returns:
            Dict con resultado de la indexación y trace de decisiones
        """
        task_description = f"""**TAREA: Indexación Completa de Directorio**

Directorio: {directory_path}
Tipos de archivo: {file_types}
Limpieza agresiva sugerida: {clean_aggressive}
Guardar índice: {save_index}

**Tu Trabajo:**
1. Escanea el directorio para ver qué documentos hay
2. Carga los documentos encontrados
3. Procesa los documentos (limpieza + chunking)
4. Verifica si existe índice activo
5. Crea índice nuevo o agrega a existente según corresponda
6. Guarda el índice si save_index=True
7. Retorna estadísticas completas

Ejecuta todas las herramientas necesarias de forma autónoma. Toma decisiones inteligentes basadas en la cantidad y tipo de documentos."""

        try:
            logger.info(f"🤖 Indexación autónoma iniciada: {directory_path}")
            
            # Invocar con formato LangChain 1.1
            result = self.agent_executor.invoke({
                "messages": [
                    {"role": "user", "content": task_description}
                ]
            })
            
            logger.info("✅ Indexación autónoma completada")
            
            # Extraer respuesta del nuevo formato de mensajes
            messages = result.get('messages', [])
            output = ""
            for msg in messages:
                if hasattr(msg, 'content') and msg.content and not hasattr(msg, 'tool_call_id'):
                    output = msg.content
            
            return {
                "status": "success",
                "response": output,
                "intermediate_steps": [],
                "directory": directory_path,
                "file_types": file_types
            }
            
        except Exception as e:
            logger.error(f"❌ Error en indexación autónoma: {e}")
            return {
                "status": "error",
                "error": str(e),
                "directory": directory_path
            }
    
    def add_documents(self,
                     file_paths: List[str],
                     clean_aggressive: bool = False,
                     save_index: bool = True) -> Dict[str, Any]:
        """
        Agrega documentos específicos al índice existente de forma autónoma.
        
        El agente decide:
        - Cómo cargar los archivos
        - Qué procesamiento aplicar
        - Si el índice existe y debe cargarse
        - Cuándo guardar cambios
        
        Args:
            file_paths: Lista de rutas de archivos a agregar
            clean_aggressive: Sugerencia de limpieza agresiva
            save_index: Si guardar el índice actualizado
            
        Returns:
            Dict con resultado de la adición y trace de decisiones
        """
        files_str = "\n".join([f"  - {fp}" for fp in file_paths])
        
        task_description = f"""**TAREA: Agregar Documentos a Índice Existente**

Archivos a agregar ({len(file_paths)}):
{files_str}

Limpieza agresiva sugerida: {clean_aggressive}
Guardar índice: {save_index}

**Tu Trabajo:**
1. Verifica que existe un índice activo (get_index_statistics)
2. Si no existe, carga el índice desde disco (load_vector_index)
3. Carga los archivos especificados (load_documents_batch)
4. Procesa los documentos (limpieza + chunking)
5. Agrega al índice existente (add_to_vector_index)
6. Guarda el índice actualizado si save_index=True
7. Retorna estadísticas de antes y después

Ejecuta de forma autónoma verificando errores en cada paso."""

        try:
            logger.info(f"🤖 Adición autónoma iniciada: {len(file_paths)} archivos")
            
            # Invocar con formato LangChain 1.1
            result = self.agent_executor.invoke({
                "messages": [
                    {"role": "user", "content": task_description}
                ]
            })
            
            logger.info("✅ Adición autónoma completada")
            
            # Extraer respuesta del nuevo formato
            messages = result.get('messages', [])
            output = ""
            for msg in messages:
                if hasattr(msg, 'content') and msg.content and not hasattr(msg, 'tool_call_id'):
                    output = msg.content
            
            return {
                "status": "success",
                "response": output,
                "intermediate_steps": [],
                "files_count": len(file_paths)
            }
            
        except Exception as e:
            logger.error(f"❌ Error en adición autónoma: {e}")
            return {
                "status": "error",
                "error": str(e),
                "files_count": len(file_paths)
            }
    
    def load_existing_index(self, index_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Carga un índice existente de forma autónoma.
        
        El agente decide:
        - Qué índice cargar
        - Cómo verificar que se cargó correctamente
        - Qué estadísticas reportar
        
        Args:
            index_name: Nombre del índice (None usa default)
            
        Returns:
            Dict con resultado de la carga y estadísticas
        """
        task_description = f"""**TAREA: Cargar Índice Existente**

Índice: {index_name if index_name else "default (config)"}

**Tu Trabajo:**
1. Carga el índice desde disco (load_vector_index)
2. Verifica que se cargó correctamente (get_index_statistics)
3. Retorna estadísticas completas del índice cargado

Simple y directo."""

        try:
            logger.info(f"🤖 Carga autónoma de índice iniciada")
            
            # Invocar con formato LangChain 1.1
            result = self.agent_executor.invoke({
                "messages": [
                    {"role": "user", "content": task_description}
                ]
            })
            
            logger.info("✅ Carga autónoma completada")
            
            # Extraer respuesta del nuevo formato
            messages = result.get('messages', [])
            output = ""
            for msg in messages:
                if hasattr(msg, 'content') and msg.content and not hasattr(msg, 'tool_call_id'):
                    output = msg.content
            
            return {
                "status": "success",
                "response": output,
                "intermediate_steps": []
            }
            
        except Exception as e:
            logger.error(f"❌ Error en carga autónoma: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del índice de forma autónoma.
        
        Returns:
            Dict con estadísticas del índice
        """
        task_description = """**TAREA: Obtener Estadísticas del Índice**

Usa get_index_statistics para obtener estadísticas del índice actual.
Retorna la información en formato claro."""

        try:
            # Invocar con formato LangChain 1.1
            result = self.agent_executor.invoke({
                "messages": [
                    {"role": "user", "content": task_description}
                ]
            })
            
            # Extraer respuesta del nuevo formato
            messages = result.get('messages', [])
            output = ""
            for msg in messages:
                if hasattr(msg, 'content') and msg.content and not hasattr(msg, 'tool_call_id'):
                    output = msg.content
            
            return {
                "status": "success",
                "response": output,
                "intermediate_steps": []
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
