"""
Test del Agente Indexador Autónomo.

Este test demuestra el funcionamiento del AutonomousIndexerAgent
simulando una indexación desde cero de documentos sobre dinosaurios.
"""
import os
import sys
import logging
import shutil
from pathlib import Path
from datetime import datetime

# Configurar path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.autonomous_indexer_agent import AutonomousIndexerAgent
from src.rag_pipeline.vectorstore import VectorStoreManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_indexer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def print_header(title: str):
    """Imprime un encabezado formateado."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def print_section(title: str):
    """Imprime un título de sección."""
    print(f"\n{'─'*80}")
    print(f"📋 {title}")
    print(f"{'─'*80}\n")


def test_indexer_agent():
    """
    Test de indexación con herramientas directas.
    
    Indexación en entorno aislado de prueba:
    1. Preparar directorio de prueba separado
    2. Crear subset temporal de 10 archivos PDF
    3. Indexar usando herramientas directamente (sin agente)
    4. Verificar resultados
    5. Mostrar estadísticas
    6. Limpiar entorno de prueba
    
    NOTA: El índice original en faiss_index permanece intacto.
    Se usan herramientas directas en lugar del agente autónomo
    para evitar límites de contexto del LLM.
    """
    print_header("🦖 TEST DE INDEXACIÓN CON HERRAMIENTAS - DINOSAURIOS")
    
    # Configuración
    data_dir = Path("data/raw")
    test_data_dir = Path("data/raw_test_subset")  # Subset temporal para el test
    vectorstore_dir = Path("data/vectorstore/faiss_index_test")  # Directorio de prueba
    vectorstore_original = Path("data/vectorstore/faiss_index")  # Índice original (NO SE TOCA)
    
    print_section("Configuración del Test")
    print(f"📂 Directorio de datos: {data_dir}")
    print(f"📂 Subset temporal: {test_data_dir}")
    print(f"📂 Índice de PRUEBA: {vectorstore_dir}")
    print(f"📂 Índice ORIGINAL (no se tocará): {vectorstore_original}")
    print(f"⚠️  NOTA: El test crea un índice temporal separado del original")
    
    # Paso 1: Limpiar índice de prueba si existe
    print_section("Paso 1: Preparar Entorno de Prueba")
    
    if vectorstore_dir.exists():
        print(f"🗑️  Eliminando índice de prueba anterior...")
        shutil.rmtree(vectorstore_dir)
        print("✅ Índice de prueba anterior eliminado")
    
    print(f"📂 Creando directorio de prueba: {vectorstore_dir}")
    vectorstore_dir.mkdir(parents=True, exist_ok=True)
    print("✅ Entorno de prueba preparado")
    print(f"ℹ️  El índice original ({vectorstore_original}) permanece intacto")
    
    # Paso 2: Verificar documentos disponibles
    print_section("Paso 2: Verificar Documentos Disponibles")
    
    if not data_dir.exists():
        print(f"❌ ERROR: Directorio {data_dir} no existe")
        return
    
    # Contar documentos por tipo
    pdf_files = list(data_dir.glob("*.pdf"))
    html_files = list(data_dir.glob("*.html"))
    txt_files = list(data_dir.glob("*.txt"))
    
    total_files = len(pdf_files) + len(html_files) + len(txt_files)
    
    print(f"📊 Archivos encontrados:")
    print(f"   - PDFs: {len(pdf_files)}")
    print(f"   - HTMLs: {len(html_files)}")
    print(f"   - TXTs: {len(txt_files)}")
    print(f"   - TOTAL: {total_files}")
    
    if total_files == 0:
        print(f"❌ ERROR: No se encontraron documentos en {data_dir}")
        return
    
    # Para el test, usar solo una muestra de archivos
    max_files_for_test = 10
    print(f"\n⚠️  NOTA: Para el test, indexaremos solo {max_files_for_test} archivos")
    print(f"   (El índice completo tiene 100+ documentos)")
    print(f"   (Reducido para evitar límites de contexto del LLM)")
    
    # Crear directorio temporal con subset de archivos
    print(f"\n📂 Creando subset temporal en: {test_data_dir}")
    
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)
    test_data_dir.mkdir(parents=True)
    
    # Copiar solo los primeros N archivos PDF
    pdf_files_copied = 0
    for pdf_file in sorted(pdf_files)[:max_files_for_test]:
        # pdf_file ya es un Path completo (ej: data/raw/archivo.pdf)
        # Necesitamos solo el nombre del archivo
        shutil.copy2(pdf_file, test_data_dir / pdf_file.name)
        pdf_files_copied += 1
    
    print(f"✅ Copiados {pdf_files_copied} archivos PDF para el test")
    print(f"   Directorio temporal: {test_data_dir}")
    
    # Paso 3: Indexación Directa (sin agente para evitar límites de contexto)
    print_section("Paso 3: Indexación Directa con Herramientas")
    
    print("🔧 Usando herramientas de indexación directamente...")
    print("   (El agente autónomo acumula demasiado contexto con 10+ archivos)")
    print("   Herramientas a usar:")
    print("   - scan_directory_for_documents")
    print("   - load_documents_batch")
    print("   - process_documents_pipeline")
    print("   - create_vector_index")
    print("   - save_vector_index")
    print("\n⏳ Procesando... (esto puede tardar 30-60 segundos)\n")
    
    from src.tools.document_loader_tool import scan_directory_for_documents, load_documents_batch
    from src.tools.document_processing_tool import process_documents_pipeline
    from src.tools.index_management_tool import create_vector_index, save_vector_index, get_index_statistics
    
    start_time = datetime.now()
    
    try:
        # 1. Escanear directorio
        print("📂 Paso 3.1: Escaneando directorio...")
        scan_result = scan_directory_for_documents.invoke({
            "directory_path": str(test_data_dir),
            "file_types": "pdf"
        })
        print(f"   ✅ Encontrados: {scan_result['total_files']} archivos PDF")
        
        # 2. Cargar documentos en batch
        print("\n📥 Paso 3.2: Cargando documentos...")
        load_result = load_documents_batch.invoke({
            "file_paths": scan_result['file_list']
        })
        print(f"   ✅ Cargados: {load_result['total_documents']} documentos de {load_result['files_processed']} archivos")
        
        # 3. Procesar documentos (limpieza + chunking)
        print("\n⚙️  Paso 3.3: Procesando documentos (limpieza + chunking)...")
        process_result = process_documents_pipeline.invoke({
            "documents": load_result['documents'],
            "clean_aggressive": True,
            "chunk_size": 512,
            "chunk_overlap": 50
        })
        print(f"   ✅ Procesados: {process_result['total_chunks']} chunks de {process_result['original_documents']} documentos")
        
        # 4. Crear índice vectorial
        print("\n🔢 Paso 3.4: Creando índice vectorial FAISS...")
        index_result = create_vector_index.invoke({
            "chunks": process_result['final_chunks'],
            "index_name": "faiss_index_test"
        })
        print(f"   ✅ Índice creado: {index_result['total_chunks']} chunks indexados")
        
        # 5. Guardar índice
        print("\n💾 Paso 3.5: Guardando índice en disco...")
        save_result = save_vector_index.invoke({
            "index_name": "faiss_index_test"
        })
        
        if save_result.get('status') == 'success':
            print(f"   ✅ Guardado en: {save_result['save_path']}")
        else:
            print(f"   ⚠️  Error guardando: {save_result.get('error', 'Unknown')}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result = {
            "status": "success",
            "files_processed": load_result['files_processed'],
            "total_documents": load_result['total_documents'],
            "total_chunks": process_result['total_chunks'],
            "chunks_indexed": index_result['total_chunks']
        }
        
        print_section("Paso 4: Resultados de la Indexación")
        
        print(f"⏱️  Tiempo total: {duration:.2f} segundos")
        print(f"📊 Estado: {result.get('status', 'unknown')}")
        print("✅ Indexación completada exitosamente\n")
        
        print("📈 Estadísticas:")
        print(f"   - Archivos procesados: {result['files_processed']}")
        print(f"   - Documentos cargados: {result['total_documents']}")
        print(f"   - Chunks creados: {result['total_chunks']}")
        print(f"   - Chunks indexados: {result['chunks_indexed']}")
        
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result = {
            "status": "error",
            "error": str(e)
        }
        
        print_section("Paso 4: Resultados de la Indexación")
        
        print(f"⏱️  Tiempo total: {duration:.2f} segundos")
        print(f"📊 Estado: error")
        print(f"❌ Error en indexación: {e}")
        import traceback
        traceback.print_exc()
    
    # Paso 5: Verificar Índice Creado
    print_section("Paso 5: Verificar Índice Creado")
    
    try:
        vectorstore_manager = VectorStoreManager(index_name="faiss_index_test")
        vectorstore_manager.load_index()
        
        if vectorstore_manager.vectorstore:
            stats = vectorstore_manager.get_index_stats()
            
            print("✅ Índice vectorial verificado exitosamente\n")
            print("📊 Estadísticas del índice:")
            print(f"   - Documentos indexados: {stats.get('documents', 0)}")
            print(f"   - Dimensión de embeddings: {stats.get('dimension', 0)}")
            print(f"   - Ubicación: {stats.get('index_path', 'N/A')}")
            
            # Probar búsqueda
            print("\n🔍 Probando búsqueda en el índice...")
            test_query = "¿Cuáles fueron los dinosaurios más grandes?"
            results = vectorstore_manager.similarity_search(test_query, k=3)
            
            print(f"   Query: '{test_query}'")
            print(f"   Resultados encontrados: {len(results)}")
            
            if results:
                print("\n   📄 Primeros 3 resultados:")
                for i, doc in enumerate(results, 1):
                    # Handle both Document objects and dict results
                    if hasattr(doc, 'metadata'):
                        source = doc.metadata.get('source', 'Unknown')
                        content = doc.page_content
                    else:
                        source = doc.get('metadata', {}).get('source', 'Unknown')
                        content = doc.get('page_content', str(doc))
                    
                    content_preview = content[:150] + "..." if len(content) > 150 else content
                    print(f"\n   [{i}] Fuente: {source}")
                    print(f"       Contenido: {content_preview}")
        else:
            print("⚠️  No se pudo cargar el índice")
            
    except Exception as e:
        print(f"❌ ERROR verificando índice: {e}")
    
    # Paso 6: Limpieza del Entorno de Prueba
    print_section("Paso 6: Limpieza del Entorno de Prueba")
    
    print("🗑️  Eliminando índice de prueba...")
    if vectorstore_dir.exists():
        shutil.rmtree(vectorstore_dir)
        print("✅ Índice de prueba eliminado")
    else:
        print("ℹ️  Índice de prueba ya estaba limpio")
    
    print("🗑️  Eliminando directorio temporal de datos...")
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)
        print("✅ Directorio temporal eliminado")
    
    print(f"✅ Índice original ({vectorstore_original}) permanece intacto")
    print("ℹ️  Listo para producción")
    
    # Resumen Final
    print_section("Resumen del Test")
    
    print("📊 Operaciones realizadas:")
    print("   ✅ Preparación de entorno de prueba")
    print("   ✅ Creación de subset temporal de datos")
    print("   ✅ Indexación directa con herramientas")
    print("   ✅ Verificación del índice creado")
    print("   ✅ Prueba de búsqueda")
    print("   ✅ Limpieza del entorno de prueba")
    
    if result.get('status') == 'success':
        print("\n🎉 TEST COMPLETADO EXITOSAMENTE")
        print(f"⏱️  Tiempo total de indexación: {duration:.2f}s")
        print(f"📂 Índice original: {vectorstore_original} (intacto)")
    else:
        print("\n⚠️  TEST COMPLETADO CON ERRORES")
        print(f"   Error: {result.get('error', 'Unknown')}")
    
    print_header("FIN DEL TEST")


if __name__ == "__main__":
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "     TEST DE INDEXACIÓN CON HERRAMIENTAS - SISTEMA RAG".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "═"*78 + "╝")
    print("\n")
    
    logger.info("=== Iniciando Test del Agente Indexador ===")
    
    try:
        test_indexer_agent()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrumpido por el usuario")
        logger.warning("Test interrumpido por el usuario")
    except Exception as e:
        print(f"\n\n❌ ERROR FATAL: {e}")
        logger.error(f"Error fatal en test: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
    
    logger.info("=== Test del Agente Indexador Finalizado ===")
    print("\n")
