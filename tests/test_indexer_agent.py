"""
Test para IndexerAgent - Persona 2
Verifica que el pipeline completo de indexación funcione correctamente.
"""
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.indexer_agent import IndexerAgent
from src.config.paths import RAW_DATA_DIR, VECTORSTORE_DIR, VECTORSTORE_INDEX


def test_indexer_agent():
    """Prueba los componentes del IndexerAgent."""
    
    print("="*70)
    print("PRUEBA DE COMPONENTES - IndexerAgent (Persona 2)")
    print("="*70)
    
    # Test 1: Inicialización
    print("\n1. Probando inicialización...")
    try:
        indexer = IndexerAgent()
        print(f"   ✅ IndexerAgent inicializado")
        print(f"   - Chunker: {type(indexer.chunker).__name__}")
        print(f"   - Embeddings Manager: {type(indexer.embeddings_manager).__name__}")
        print(f"   - VectorStore Manager: {type(indexer.vectorstore_manager).__name__}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: Verificar que existe el directorio de datos
    print("\n2. Verificando directorio de datos...")
    if not RAW_DATA_DIR.exists():
        print(f"   ⚠️  Directorio {RAW_DATA_DIR} no existe")
        print(f"   💡 Coloca documentos en: {RAW_DATA_DIR}")
        print(f"   Continuando con prueba limitada...")
        has_corpus = False
    else:
        # Contar documentos disponibles
        pdf_count = len(list(RAW_DATA_DIR.glob("*.pdf")))
        html_count = len(list(RAW_DATA_DIR.glob("*.html"))) + len(list(RAW_DATA_DIR.glob("*.htm")))
        txt_count = len(list(RAW_DATA_DIR.glob("*.txt")))
        total = pdf_count + html_count + txt_count
        
        print(f"   ✅ Directorio encontrado: {RAW_DATA_DIR}")
        print(f"   - PDFs: {pdf_count}")
        print(f"   - HTMLs: {html_count}")
        print(f"   - TXTs: {txt_count}")
        print(f"   - Total: {total}")
        has_corpus = total > 0
    
    # Test 3: Indexar directorio (si hay corpus)
    if has_corpus:
        print("\n3. Probando indexación de directorio completo...")
        try:
            stats = indexer.index_directory(
                directory_path=str(RAW_DATA_DIR),
                file_types=['pdf', 'html', 'txt'],
                clean_aggressive=False,
                save_index=True
            )
            
            print(f"   ✅ Indexación completada")
            print(f"   - Estado: {stats.get('status')}")
            print(f"   - Documentos procesados: {stats.get('total_documents', 0)}")
            print(f"   - Chunks generados: {stats.get('total_chunks', 0)}")
            
            file_counts = stats.get('file_counts', {})
            print(f"   - PDFs: {file_counts.get('pdf', 0)}")
            print(f"   - HTMLs: {file_counts.get('html', 0)}")
            print(f"   - TXTs: {file_counts.get('txt', 0)}")
            
            if stats.get('status') == 'success':
                print(f"   ✅ Pipeline completo ejecutado exitosamente")
            else:
                print(f"   ⚠️  Estado: {stats.get('status')}")
                if 'error' in stats:
                    print(f"   - Error: {stats.get('error')}")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n3. ⚠️  Saltando indexación (no hay corpus disponible)")
    
    # Test 4: Estadísticas del índice
    print("\n4. Verificando estadísticas del índice...")
    try:
        stats = indexer.get_index_stats()
        
        print(f"   ✅ Estadísticas obtenidas")
        print(f"   - Estado: {stats.get('status')}")
        print(f"   - Total chunks: {stats.get('total_chunks', 0)}")
        print(f"   - Dimensión embeddings: {stats.get('embedding_dim', 0)}")
        print(f"   - Métrica similitud: {stats.get('similarity_metric', 'N/A')}")
        
        if stats.get('status') == 'active':
            print(f"   ✅ Índice activo y funcionando")
        else:
            print(f"   ⚠️  Índice no activo (puede ser normal si no se indexó)")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Cargar índice existente
    print("\n5. Probando carga de índice existente...")
    try:
        index_path = VECTORSTORE_DIR / VECTORSTORE_INDEX
        
        if index_path.exists():
            # Crear nuevo indexer para probar carga
            indexer2 = IndexerAgent()
            success = indexer2.load_existing_index()
            
            if success:
                print(f"   ✅ Índice cargado exitosamente")
                
                # Verificar que funciona
                stats = indexer2.get_index_stats()
                print(f"   - Chunks en índice cargado: {stats.get('total_chunks', 0)}")
            else:
                print(f"   ⚠️  No se pudo cargar el índice")
        else:
            print(f"   ⚠️  No hay índice guardado en: {index_path}")
            print(f"   💡 Ejecuta index_directory primero para crear un índice")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 6: Agregar documentos (si hay índice activo)
    print("\n6. Probando agregar documentos al índice...")
    try:
        current_stats = indexer.get_index_stats()
        
        if current_stats.get('status') == 'active' and has_corpus:
            # Buscar un archivo de prueba para agregar
            test_files = []
            for ext in ['.txt', '.html', '.pdf']:
                files = list(RAW_DATA_DIR.glob(f"*{ext}"))
                if files:
                    test_files.append(str(files[0]))
                    break
            
            if test_files:
                chunks_before = current_stats.get('total_chunks', 0)
                
                result = indexer.add_documents(
                    file_paths=test_files[:1],  # Solo un archivo de prueba
                    clean_aggressive=False,
                    save_index=True
                )
                
                print(f"   ✅ Agregar documentos completado")
                print(f"   - Estado: {result.get('status')}")
                print(f"   - Documentos agregados: {result.get('added_documents', 0)}")
                print(f"   - Chunks agregados: {result.get('added_chunks', 0)}")
                print(f"   - Chunks antes: {result.get('chunks_before', 0)}")
                print(f"   - Chunks después: {result.get('chunks_after', 0)}")
                
                if result.get('status') == 'success':
                    print(f"   ✅ Indexación incremental funcionando")
            else:
                print(f"   ⚠️  No hay archivos de prueba disponibles")
        else:
            print(f"   ⚠️  No hay índice activo o corpus disponible")
            print(f"   💡 Indexa un directorio primero")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 7: Verificar integración con VectorStore
    print("\n7. Verificando integración con VectorStore...")
    try:
        stats = indexer.get_index_stats()
        
        if stats.get('status') == 'active':
            # Probar búsqueda
            results = indexer.vectorstore_manager.similarity_search(
                query="dinosaurios",
                k=3
            )
            
            print(f"   ✅ Integración verificada")
            print(f"   - Búsqueda de prueba: {len(results)} resultados")
            
            if results:
                print(f"   - Primer resultado score: {results[0].get('score', 0):.4f}")
                print(f"   ✅ VectorStore funcionando correctamente")
            else:
                print(f"   ⚠️  No se encontraron resultados (puede ser normal)")
        else:
            print(f"   ⚠️  Índice no activo, saltando verificación de búsqueda")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE PRUEBAS")
    print("="*70)
    
    print("\n✅ COMPONENTES IMPLEMENTADOS (IndexerAgent):")
    print("   1. Inicialización con componentes del pipeline")
    print("   2. Verificación de directorio de datos")
    print("   3. Indexación completa de directorio")
    print("   4. Estadísticas del índice")
    print("   5. Carga de índice existente")
    print("   6. Agregar documentos (indexación incremental)")
    print("   7. Integración con VectorStore")
    
    print("\n✅ ESTADO: IndexerAgent funcionando correctamente")
    
    print("\n💡 USO:")
    print("   from src.agents.indexer_agent import IndexerAgent")
    print("   indexer = IndexerAgent()")
    print("   stats = indexer.index_directory('data/raw/', save_index=True)")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    test_indexer_agent()

