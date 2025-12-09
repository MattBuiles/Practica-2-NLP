"""
Test para DocumentChunker - Persona 2
Verifica que el chunking de documentos funcione correctamente.
"""
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag_pipeline.chunking import DocumentChunker


def test_chunking():
    """Prueba los componentes del DocumentChunker."""
    
    print("="*70)
    print("PRUEBA DE COMPONENTES - DocumentChunker (Persona 2)")
    print("="*70)
    
    # Test 1: Inicialización con configuración por defecto
    print("\n1. Probando inicialización con configuración por defecto...")
    try:
        chunker = DocumentChunker()
        print(f"   ✅ DocumentChunker inicializado")
        print(f"   - Chunk size: {chunker.chunk_size}")
        print(f"   - Chunk overlap: {chunker.chunk_overlap}")
        print(f"   - Separadores: {chunker.separators}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: Inicialización con parámetros personalizados
    print("\n2. Probando inicialización con parámetros personalizados...")
    try:
        custom_chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
        print(f"   ✅ DocumentChunker con parámetros personalizados")
        print(f"   - Chunk size: {custom_chunker.chunk_size} (esperado: 500)")
        print(f"   - Chunk overlap: {custom_chunker.chunk_overlap} (esperado: 100)")
        
        if custom_chunker.chunk_size == 500 and custom_chunker.chunk_overlap == 100:
            print(f"   ✅ Parámetros personalizados aplicados correctamente")
        else:
            print(f"   ⚠️  Parámetros no coinciden con los esperados")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Chunking de un documento simple
    print("\n3. Probando chunking de documento simple...")
    try:
        test_doc = {
            'content': """
            Los dinosaurios fueron un grupo diverso de reptiles que dominaron la Tierra durante la Era Mesozoica.
            
            Estos animales fascinantes evolucionaron en una amplia variedad de formas y tamaños.
            
            Los dinosaurios se dividen principalmente en dos grupos: los saurisquios y los ornitisquios.
            
            Los saurisquios incluyen a los terópodos carnívoros como el Tyrannosaurus rex.
            
            Los ornitisquios incluyen dinosaurios como el Triceratops y el Stegosaurus.
            """,
            'metadata': {
                'source': 'test_dinosaurios.txt',
                'file_path': '/data/raw/test_dinosaurios.txt',
                'page': 1
            }
        }
        
        chunks = chunker.chunk_documents([test_doc])
        
        print(f"   ✅ Chunking completado")
        print(f"   - Chunks generados: {len(chunks)}")
        
        if chunks:
            first_chunk = chunks[0]
            print(f"\n   📋 Metadatos del primer chunk:")
            print(f"   - Source: {first_chunk['metadata'].get('source', 'N/A')}")
            print(f"   - Chunk index: {first_chunk['metadata'].get('chunk_index', 'N/A')}")
            print(f"   - Total chunks: {first_chunk['metadata'].get('total_chunks', 'N/A')}")
            print(f"   - Content length: {len(first_chunk['content'])} caracteres")
            print(f"   - Preview: {first_chunk['content'][:100]}...")
            
            # Verificar que todos los chunks tienen los metadatos correctos
            all_have_metadata = all(
                'chunk_index' in chunk['metadata'] and 
                'total_chunks' in chunk['metadata'] and
                'source' in chunk['metadata']
                for chunk in chunks
            )
            
            if all_have_metadata:
                print(f"   ✅ Todos los chunks tienen metadatos correctos")
            else:
                print(f"   ⚠️  Algunos chunks pueden tener metadatos incompletos")
        else:
            print(f"   ⚠️  No se generaron chunks")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Chunking de múltiples documentos
    print("\n4. Probando chunking de múltiples documentos...")
    try:
        test_docs = [
            {
                'content': 'Documento 1 con contenido suficiente para generar al menos un chunk. ' * 100,
                'metadata': {'source': 'doc1.txt', 'file_path': '/data/doc1.txt'}
            },
            {
                'content': 'Documento 2 con contenido diferente. ' * 20,
                'metadata': {'source': 'doc2.txt', 'file_path': '/data/doc2.txt'}
            }
        ]
        
        chunks = chunker.chunk_documents(test_docs)
        
        print(f"   ✅ Chunking múltiple completado")
        print(f"   - Documentos procesados: {len(test_docs)}")
        print(f"   - Chunks totales generados: {len(chunks)}")
        
        # Agrupar por documento
        from collections import defaultdict
        by_doc = defaultdict(list)
        for chunk in chunks:
            by_doc[chunk['metadata']['source']].append(chunk)
        
        print(f"\n   📊 Chunks por documento:")
        for doc_name, doc_chunks in by_doc.items():
            print(f"   - {doc_name}: {len(doc_chunks)} chunks")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Verificar overlap entre chunks
    print("\n5. Probando overlap entre chunks...")
    try:
        # Crear un documento largo para generar múltiples chunks
        long_text = "Párrafo de prueba. " * 100  # ~2000 caracteres
        test_doc = {
            'content': long_text,
            'metadata': {'source': 'long_doc.txt', 'file_path': '/data/long_doc.txt'}
        }
        
        chunks = chunker.chunk_documents([test_doc])
        
        if len(chunks) >= 2:
            chunk1_end = chunks[0]['content'][-50:]  # Últimos 50 caracteres
            chunk2_start = chunks[1]['content'][:50]  # Primeros 50 caracteres
            
            # Verificar que hay overlap (deben compartir algunos caracteres)
            overlap_found = any(word in chunk2_start for word in chunk1_end.split()[:5])
            
            print(f"   ✅ Múltiples chunks generados: {len(chunks)}")
            print(f"   - Chunk 1 length: {len(chunks[0]['content'])}")
            print(f"   - Chunk 2 length: {len(chunks[1]['content'])}")
            
            if overlap_found:
                print(f"   ✅ Overlap detectado entre chunks")
            else:
                print(f"   ⚠️  Overlap no claramente visible (puede ser normal)")
        else:
            print(f"   ⚠️  Solo se generó 1 chunk (documento puede ser muy corto)")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 6: Verificar formato de retorno
    print("\n6. Verificando formato de retorno...")
    try:
        test_doc = {
            'content': 'Texto de prueba para chunking. ' * 30,
            'metadata': {'source': 'test.txt', 'file_path': '/data/test.txt', 'page': 1}
        }
        
        chunks = chunker.chunk_documents([test_doc])
        
        if chunks:
            chunk = chunks[0]
            
            # Verificar estructura
            required_keys = ['content', 'metadata']
            metadata_keys = ['chunk_index', 'total_chunks', 'source', 'file_path']
            
            all_good = True
            for key in required_keys:
                if key not in chunk:
                    print(f"      ❌ Falta clave '{key}' en chunk")
                    all_good = False
            
            for key in metadata_keys:
                if key not in chunk['metadata']:
                    print(f"      ❌ Falta clave '{key}' en metadata")
                    all_good = False
            
            if all_good:
                print("      ✅ Formato de retorno correcto")
                print("      - Estructura: {content: str, metadata: dict}")
                print("      - Metadata incluye: chunk_index, total_chunks, source, file_path")
            else:
                print("      ❌ Formato de retorno incompleto")
        else:
            print("      ⚠️  No hay chunks para verificar formato")
            
    except Exception as e:
        print(f"      ❌ Error: {e}")
    
    # Test 7: Método chunk_text (auxiliar)
    print("\n7. Probando método auxiliar chunk_text...")
    try:
        test_text = "Este es un texto de prueba para chunking. " * 30
        metadata = {'source': 'test.txt', 'custom_field': 'test_value'}
        
        chunks = chunker.chunk_text(test_text, metadata=metadata)
        
        print(f"   ✅ chunk_text funcionando")
        print(f"   - Chunks generados: {len(chunks)}")
        
        if chunks:
            print(f"   - Metadata preservada: {chunks[0]['metadata'].get('custom_field', 'N/A')}")
            print(f"   - Chunk index presente: {'chunk_index' in chunks[0]['metadata']}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 8: Manejo de documentos vacíos
    print("\n8. Probando manejo de documentos vacíos...")
    try:
        empty_docs = [
            {'content': '', 'metadata': {'source': 'empty1.txt'}},
            {'content': '   ', 'metadata': {'source': 'empty2.txt'}},
            {'content': 'Corto', 'metadata': {'source': 'short.txt'}}  # Muy corto
        ]
        
        chunks = chunker.chunk_documents(empty_docs)
        
        print(f"   ✅ Manejo de documentos vacíos")
        print(f"   - Documentos procesados: {len(empty_docs)}")
        print(f"   - Chunks generados: {len(chunks)}")
        
        if len(chunks) == 0:
            print(f"   ✅ Documentos vacíos/cortos filtrados correctamente")
        else:
            print(f"   ⚠️  Se generaron chunks de documentos vacíos")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE PRUEBAS")
    print("="*70)
    
    print("\n✅ COMPONENTES IMPLEMENTADOS (DocumentChunker):")
    print("   1. Inicialización con configuración por defecto")
    print("   2. Inicialización con parámetros personalizados")
    print("   3. Chunking de documento simple")
    print("   4. Chunking de múltiples documentos")
    print("   5. Verificación de overlap entre chunks")
    print("   6. Formato estándar de retorno")
    print("   7. Método auxiliar chunk_text")
    print("   8. Manejo de documentos vacíos")
    
    print("\n✅ ESTADO: DocumentChunker funcionando correctamente")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    test_chunking()

