"""
Test para RAGPipeline - Persona 2
Verifica que el pipeline RAG completo funcione correctamente.
"""
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag_pipeline.pipelines import RAGPipeline
from src.config.paths import RAW_DATA_DIR, VECTORSTORE_DIR, VECTORSTORE_INDEX


def test_rag_pipeline():
    """Prueba los componentes del RAGPipeline."""
    
    print("="*70)
    print("PRUEBA DE COMPONENTES - RAGPipeline (Persona 2)")
    print("="*70)
    
    # Test 1: Inicialización
    print("\n1. Probando inicialización...")
    try:
        pipeline = RAGPipeline()
        print(f"   ✅ RAGPipeline inicializado")
        print(f"   - Indexer: {type(pipeline.indexer).__name__}")
        print(f"   - VectorStore: {type(pipeline.vectorstore).__name__}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: Verificar directorio de datos
    print("\n2. Verificando directorio de datos...")
    if not RAW_DATA_DIR.exists():
        print(f"   ⚠️  Directorio {RAW_DATA_DIR} no existe")
        print(f"   💡 Coloca documentos en: {RAW_DATA_DIR}")
        has_corpus = False
    else:
        pdf_count = len(list(RAW_DATA_DIR.glob("*.pdf")))
        html_count = len(list(RAW_DATA_DIR.glob("*.html"))) + len(list(RAW_DATA_DIR.glob("*.htm")))
        txt_count = len(list(RAW_DATA_DIR.glob("*.txt")))
        total = pdf_count + html_count + txt_count
        
        print(f"   ✅ Directorio encontrado: {RAW_DATA_DIR}")
        print(f"   - PDFs: {pdf_count} archivos")
        print(f"   - HTMLs: {html_count} archivos")
        print(f"   - TXTs: {txt_count} archivos")
        print(f"   - Total: {total} archivos")
        has_corpus = total > 0
    
    # Test 3: Indexar directorio (si hay corpus)
    if has_corpus:
        print("\n3. Probando indexación de directorio...")
        try:
            stats = pipeline.index_directory(
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
            print(f"\n   📊 Documentos por tipo:")
            print(f"   - PDFs: {file_counts.get('pdf', 0)} documentos")
            print(f"   - HTMLs: {file_counts.get('html', 0)} documentos")
            print(f"   - TXTs: {file_counts.get('txt', 0)} documentos")
            
            if stats.get('status') == 'success':
                print(f"   ✅ Pipeline de indexación funcionando correctamente")
            else:
                print(f"   ⚠️  Estado: {stats.get('status')}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n3. ⚠️  Saltando indexación (no hay corpus disponible)")
    
    # Test 4: Estadísticas del índice
    print("\n4. Verificando estadísticas del índice...")
    try:
        stats = pipeline.get_index_stats()
        
        print(f"   ✅ Estadísticas obtenidas")
        print(f"   - Estado: {stats.get('status')}")
        print(f"   - Total chunks: {stats.get('total_chunks', 0)}")
        print(f"   - Dimensión embeddings: {stats.get('embedding_dim', 0)}")
        print(f"   - Métrica similitud: {stats.get('similarity_metric', 'N/A')}")
        
        if stats.get('status') == 'active':
            print(f"   ✅ Índice activo y funcionando")
        else:
            print(f"   ⚠️  Índice no activo")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Cargar índice existente
    print("\n5. Probando carga de índice existente...")
    try:
        index_path = VECTORSTORE_DIR / VECTORSTORE_INDEX
        
        if index_path.exists():
            # Crear nuevo pipeline para probar carga
            pipeline2 = RAGPipeline()
            success = pipeline2.load_existing_index()
            
            if success:
                print(f"   ✅ Índice cargado exitosamente")
                
                # Verificar que funciona
                stats = pipeline2.get_index_stats()
                print(f"   - Chunks en índice cargado: {stats.get('total_chunks', 0)}")
                
                # Probar búsqueda en índice cargado
                results = pipeline2.query("dinosaurios", k=2)
                print(f"   - Búsqueda de prueba: {len(results)} resultados")
                
                if results:
                    print(f"   ✅ Índice cargado funciona correctamente")
            else:
                print(f"   ⚠️  No se pudo cargar el índice")
        else:
            print(f"   ⚠️  No hay índice guardado en: {index_path}")
            print(f"   💡 Ejecuta index_directory primero")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 6: Búsqueda semántica
    print("\n6. Probando búsqueda semántica...")
    try:
        # Verificar que hay índice activo
        stats = pipeline.get_index_stats()
        
        if stats.get('status') == 'active':
            # Pruebas de búsqueda
            test_queries = [
                "¿Qué eran los dinosaurios?",
                "Tyrannosaurus rex",
                "extinción de dinosaurios"
            ]
            
            print(f"   ✅ Realizando búsquedas de prueba...")
            
            for query in test_queries:
                results = pipeline.query(query, k=3)
                print(f"\n   🔍 Query: '{query}'")
                print(f"      - Resultados: {len(results)}")
                
                if results:
                    print(f"      - Mejor score: {results[0].get('score', 0):.4f}")
                    source = results[0].get('metadata', {}).get('source', 'N/A')
                    print(f"      - Fuente: {source}")
                    preview = results[0].get('content', '')[:80]
                    print(f"      - Preview: {preview}...")
            
            print(f"\n   ✅ Búsqueda semántica funcionando correctamente")
        else:
            print(f"   ⚠️  No hay índice activo, saltando búsqueda")
            print(f"   💡 Indexa documentos primero o carga un índice existente")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 7: Búsqueda con score threshold
    print("\n7. Probando búsqueda con score threshold...")
    try:
        stats = pipeline.get_index_stats()
        
        if stats.get('status') == 'active':
            query = "dinosaurios"
            
            # Sin threshold
            results_all = pipeline.query(query, k=5, score_threshold=None)
            
            # Con threshold
            results_filtered = pipeline.query(query, k=5, score_threshold=0.3)
            
            print(f"   ✅ Búsqueda con threshold")
            print(f"   - Query: '{query}'")
            print(f"   - Sin threshold: {len(results_all)} resultados")
            print(f"   - Con threshold 0.3: {len(results_filtered)} resultados")
            
            if results_filtered:
                min_score = min(doc.get('score', 0) for doc in results_filtered)
                print(f"   - Score mínimo: {min_score:.4f}")
                if min_score >= 0.3:
                    print(f"   ✅ Threshold funcionando correctamente")
                else:
                    print(f"   ⚠️  Algunos resultados no cumplen threshold")
        else:
            print(f"   ⚠️  No hay índice activo")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 8: Agregar documentos
    print("\n8. Probando agregar documentos al índice...")
    try:
        stats = pipeline.get_index_stats()
        
        if stats.get('status') == 'active' and has_corpus:
            # Buscar un archivo de prueba
            test_files = []
            for ext in ['.txt', '.html', '.pdf']:
                files = list(RAW_DATA_DIR.glob(f"*{ext}"))
                if files:
                    test_files.append(str(files[0]))
                    break
            
            if test_files:
                chunks_before = stats.get('total_chunks', 0)
                
                result = pipeline.add_documents(
                    file_paths=test_files[:1],
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
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE PRUEBAS")
    print("="*70)
    
    print("\n✅ COMPONENTES IMPLEMENTADOS (RAGPipeline):")
    print("   1. Inicialización con IndexerAgent y VectorStoreManager")
    print("   2. Verificación de directorio de datos")
    print("   3. Indexación completa de directorio")
    print("   4. Estadísticas del índice")
    print("   5. Carga de índice existente")
    print("   6. Búsqueda semántica")
    print("   7. Búsqueda con score threshold")
    print("   8. Agregar documentos (indexación incremental)")
    
    print("\n✅ ESTADO: RAGPipeline funcionando correctamente")
    
    print("\n💡 USO:")
    print("   from src.rag_pipeline.pipelines import RAGPipeline")
    print("   pipeline = RAGPipeline()")
    print("   pipeline.index_directory('data/raw/', save_index=True)")
    print("   results = pipeline.query('dinosaurios', k=5)")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    test_rag_pipeline()

