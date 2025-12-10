"""
Demo de Indexación - Agente Indexador
Demuestra el proceso completo de indexación de documentos en vector store.
"""
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.indexer_agent import IndexerAgent
from src.config.paths import RAW_DATA_DIR, VECTORSTORE_DIR, VECTORSTORE_INDEX


def print_section(title):
    """Imprime sección con formato."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def demo_indexacion(reset_index=False, limit_files=None):
    """
    Ejecuta una demostración completa del proceso de indexación.
    
    Args:
        reset_index: Si True, elimina el índice existente antes de indexar
        limit_files: Número máximo de archivos a indexar (None = todos)
    """
    start_time = datetime.now()
    
    print_section("🔍 DEMO: AGENTE INDEXADOR - PROCESO COMPLETO DE INDEXACIÓN")
    
    print(f"\n📅 Fecha: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Corpus: {RAW_DATA_DIR}")
    print(f"💾 Vector Store: {VECTORSTORE_DIR / VECTORSTORE_INDEX}")
    
    # Paso 1: Verificar corpus
    print_section("PASO 1: Verificación del Corpus")
    
    if not RAW_DATA_DIR.exists():
        print(f"\n❌ ERROR: Directorio de datos no existe: {RAW_DATA_DIR}")
        print(f"💡 Crea el directorio y coloca documentos allí")
        return
    
    # Contar archivos por tipo
    pdf_files = list(RAW_DATA_DIR.glob("*.pdf"))
    html_files = list(RAW_DATA_DIR.glob("*.html")) + list(RAW_DATA_DIR.glob("*.htm"))
    txt_files = list(RAW_DATA_DIR.glob("*.txt"))
    
    total_files = len(pdf_files) + len(html_files) + len(txt_files)
    
    print(f"\n📊 Archivos encontrados en corpus:")
    print(f"   📄 PDFs: {len(pdf_files)} archivos")
    print(f"   🌐 HTMLs: {len(html_files)} archivos")
    print(f"   📝 TXTs: {len(txt_files)} archivos")
    print(f"   ✅ TOTAL: {total_files} archivos")
    
    if total_files == 0:
        print(f"\n❌ ERROR: No hay archivos para indexar")
        print(f"💡 Coloca archivos PDF, HTML o TXT en: {RAW_DATA_DIR}")
        return
    
    # Aplicar límite si se especificó
    if limit_files and limit_files < total_files:
        print(f"\n⚠️  Limitando a {limit_files} archivos (modo demo)")
    
    # Paso 2: Verificar índice existente
    print_section("PASO 2: Verificación de Índice Existente")
    
    index_path = VECTORSTORE_DIR / VECTORSTORE_INDEX
    index_exists = index_path.exists()
    
    if index_exists:
        print(f"\n✅ Índice existente encontrado: {index_path}")
        
        # Cargar para ver estadísticas
        temp_indexer = IndexerAgent()
        temp_indexer.load_existing_index()
        stats = temp_indexer.get_index_stats()
        
        print(f"\n📊 Estadísticas del índice actual:")
        print(f"   - Estado: {stats.get('status', 'unknown')}")
        print(f"   - Chunks indexados: {stats.get('total_chunks', 0):,}")
        print(f"   - Dimensión: {stats.get('embedding_dim', 0)}")
        print(f"   - Métrica: {stats.get('similarity_metric', 'N/A')}")
        
        if reset_index:
            print(f"\n⚠️  Eliminando índice existente (--reset-index activado)...")
            shutil.rmtree(index_path)
            print(f"   ✅ Índice eliminado")
        else:
            print(f"\n💡 El nuevo contenido se agregará al índice existente")
            print(f"💡 Usa --reset-index para empezar desde cero")
    else:
        print(f"\n📝 No hay índice existente")
        print(f"   Se creará un nuevo índice en: {index_path}")
    
    # Paso 3: Inicializar Agente Indexador
    print_section("PASO 3: Inicialización del Agente Indexador")
    
    try:
        indexer = IndexerAgent()
        print(f"\n✅ IndexerAgent inicializado correctamente")
        print(f"\n🔧 Componentes del pipeline:")
        print(f"   - DocumentChunker: {type(indexer.chunker).__name__}")
        print(f"     • Chunk size: {indexer.chunker.chunk_size} caracteres")
        print(f"     • Overlap: {indexer.chunker.chunk_overlap} caracteres")
        print(f"   - EmbeddingsManager: {type(indexer.embeddings_manager).__name__}")
        print(f"     • Modelo: {indexer.embeddings_manager.model_name}")
        print(f"     • Dimensión: {indexer.embeddings_manager.dimension}")
        print(f"   - VectorStoreManager: {type(indexer.vectorstore_manager).__name__}")
        print(f"     • Índice: {indexer.vectorstore_manager.index_name}")
    except Exception as e:
        print(f"\n❌ ERROR al inicializar: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Paso 4: Proceso de Indexación
    print_section("PASO 4: Indexación de Documentos")
    
    print(f"\n🚀 Iniciando indexación...")
    print(f"   Esto puede tomar varios minutos dependiendo del corpus...")
    
    try:
        # Indexar directorio completo
        stats = indexer.index_directory(
            directory_path=str(RAW_DATA_DIR),
            file_types=['pdf', 'html', 'txt'],
            clean_aggressive=False,
            save_index=True,
            max_files=limit_files
        )
        
        indexation_time = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✅ Indexación completada en {indexation_time:.2f} segundos")
        
        print(f"\n📊 Resultados de la indexación:")
        print(f"   - Estado: {stats.get('status')}")
        print(f"   - Archivos procesados: {stats.get('files_processed', 0)}")
        print(f"   - Documentos generados: {stats.get('total_documents', 0):,}")
        print(f"   - Chunks totales: {stats.get('total_chunks', 0):,}")
        print(f"   - Tiempo: {indexation_time:.2f}s")
        
        # Desglose por tipo
        file_counts = stats.get('file_counts', {})
        if file_counts:
            print(f"\n📂 Desglose por tipo de archivo:")
            for file_type, count in file_counts.items():
                print(f"   - {file_type.upper()}: {count:,} documentos")
        
        # Mostrar información del índice final
        if stats.get('status') == 'success':
            final_stats = indexer.get_index_stats()
            print(f"\n💾 Estado final del Vector Store:")
            print(f"   - Total chunks en índice: {final_stats.get('total_chunks', 0):,}")
            print(f"   - Dimensión embeddings: {final_stats.get('embedding_dim', 0)}")
            print(f"   - Tamaño aproximado: {final_stats.get('index_size_mb', 0):.2f} MB")
            
    except Exception as e:
        print(f"\n❌ ERROR durante indexación: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Paso 5: Verificación del índice
    print_section("PASO 5: Verificación del Vector Store")
    
    try:
        # Probar búsqueda
        print(f"\n🔍 Probando búsqueda en el vector store...")
        
        test_queries = [
            "dinosaurios más grandes",
            "Tyrannosaurus rex",
            "extinción"
        ]
        
        for i, query in enumerate(test_queries, 1):
            results = indexer.vectorstore_manager.similarity_search(
                query=query,
                k=3
            )
            
            print(f"\n   Query {i}: '{query}'")
            print(f"   - Resultados: {len(results)}")
            
            if results:
                print(f"   - Top result score: {results[0].get('score', 0):.4f}")
                content_preview = results[0].get('content', '')[:100].replace('\n', ' ')
                print(f"   - Preview: {content_preview}...")
        
        print(f"\n✅ Vector store funcionando correctamente")
        
    except Exception as e:
        print(f"\n❌ ERROR en verificación: {e}")
        import traceback
        traceback.print_exc()
    
    # Paso 6: Cargar índice existente (test de persistencia)
    print_section("PASO 6: Test de Persistencia")
    
    try:
        print(f"\n🔄 Creando nuevo agente y cargando índice...")
        
        new_indexer = IndexerAgent()
        success = new_indexer.load_existing_index()
        
        if success:
            stats = new_indexer.get_index_stats()
            print(f"   ✅ Índice cargado exitosamente")
            print(f"   - Chunks recuperados: {stats.get('total_chunks', 0):,}")
            print(f"   💾 Persistencia verificada: El índice se guardó correctamente")
        else:
            print(f"   ❌ No se pudo cargar el índice")
            
    except Exception as e:
        print(f"\n❌ ERROR en test de persistencia: {e}")
        import traceback
        traceback.print_exc()
    
    # Resumen final
    total_time = (datetime.now() - start_time).total_seconds()
    
    print_section("✅ DEMO COMPLETADA")
    
    print(f"\n🎯 Resumen:")
    print(f"   - Tiempo total: {total_time:.2f} segundos")
    print(f"   - Archivos en corpus: {total_files}")
    print(f"   - Documentos indexados: {stats.get('total_documents', 0):,}")
    print(f"   - Chunks en vector store: {stats.get('total_chunks', 0):,}")
    print(f"   - Índice guardado en: {index_path}")
    
    print(f"\n📖 Próximos pasos:")
    print(f"   1. Ejecuta test_dinosaurios.py para probar el sistema RAG completo")
    print(f"   2. Ejecuta 'streamlit run ui_dinosaurios.py' para la interfaz web")
    print(f"   3. Usa main.py para consultas interactivas")
    
    print(f"\n💡 Para reindexar desde cero:")
    print(f"   python test_indexacion_demo.py --reset-index")
    
    print("\n" + "="*80)


def main():
    """Función principal con argumentos."""
    parser = argparse.ArgumentParser(
        description='Demo de indexación del Agente Indexador',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python test_indexacion_demo.py                    # Indexar todo
  python test_indexacion_demo.py --reset-index      # Eliminar índice y reindexar
  python test_indexacion_demo.py --limit 20         # Indexar solo 20 archivos
  python test_indexacion_demo.py --reset --limit 10 # Reindexar solo 10 archivos
        """
    )
    
    parser.add_argument(
        '--reset-index',
        '--reset',
        action='store_true',
        help='Elimina el índice existente antes de indexar'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limitar número de archivos a indexar (útil para demos rápidas)'
    )
    
    args = parser.parse_args()
    
    # Ejecutar demo
    demo_indexacion(
        reset_index=args.reset_index,
        limit_files=args.limit
    )


if __name__ == "__main__":
    main()
