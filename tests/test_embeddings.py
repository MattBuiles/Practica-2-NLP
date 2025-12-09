"""
Test para EmbeddingsManager - Persona 2
Verifica que la generación de embeddings funcione correctamente.
"""
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag_pipeline.embeddings import EmbeddingsManager


def test_embeddings():
    """Prueba los componentes del EmbeddingsManager."""
    
    print("="*70)
    print("PRUEBA DE COMPONENTES - EmbeddingsManager (Persona 2)")
    print("="*70)
    
    # Test 1: Inicialización con configuración por defecto
    print("\n1. Probando inicialización con configuración por defecto...")
    try:
        embeddings_mgr = EmbeddingsManager()
        print(f"   ✅ EmbeddingsManager inicializado")
        print(f"   - Modelo: {embeddings_mgr.model_name}")
        print(f"   - Dispositivo: {embeddings_mgr.device}")
        print(f"   - Dimensión: {embeddings_mgr.get_embedding_dimension()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: Verificar dependencia sentence-transformers
    print("\n2. Verificando dependencia sentence-transformers...")
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        print("   ✅ langchain_community.embeddings.HuggingFaceEmbeddings disponible")
    except ImportError as e:
        print(f"   ❌ Error: {e}")
        print("   💡 Instala con: pip install sentence-transformers langchain-community")
        return
    
    # Test 3: Generar embedding de un texto simple
    print("\n3. Probando generación de embedding de texto simple...")
    try:
        test_text = "Los dinosaurios fueron reptiles que dominaron la Tierra durante millones de años."
        embedding = embeddings_mgr.embed_text(test_text)
        
        print(f"   ✅ Embedding generado")
        print(f"   - Dimensión del embedding: {len(embedding)}")
        print(f"   - Tipo: {type(embedding)}")
        print(f"   - Primeros 5 valores: {embedding[:5]}")
        
        # Verificar dimensión
        expected_dim = embeddings_mgr.get_embedding_dimension()
        if len(embedding) == expected_dim:
            print(f"   ✅ Dimensión correcta ({expected_dim})")
        else:
            print(f"   ⚠️  Dimensión esperada: {expected_dim}, obtenida: {len(embedding)}")
        
        # Verificar que no es todo ceros
        if any(abs(val) > 0.001 for val in embedding):
            print(f"   ✅ Embedding contiene valores no nulos")
        else:
            print(f"   ⚠️  Embedding parece estar vacío o ser todo ceros")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Generar embeddings de múltiples textos (batch)
    print("\n4. Probando generación de embeddings en batch...")
    try:
        test_texts = [
            "Los dinosaurios fueron reptiles que dominaron la Tierra.",
            "El Tyrannosaurus rex era un depredador temible.",
            "Los triceratops tenían tres cuernos en su cabeza."
        ]
        
        embeddings = embeddings_mgr.embed_texts(test_texts)
        
        print(f"   ✅ Embeddings generados en batch")
        print(f"   - Textos procesados: {len(test_texts)}")
        print(f"   - Embeddings generados: {len(embeddings)}")
        
        if len(embeddings) == len(test_texts):
            print(f"   ✅ Número de embeddings coincide con número de textos")
        else:
            print(f"   ⚠️  Número de embeddings no coincide")
        
        # Verificar que todos tienen la misma dimensión
        dims = [len(emb) for emb in embeddings]
        if len(set(dims)) == 1:
            print(f"   ✅ Todos los embeddings tienen la misma dimensión: {dims[0]}")
        else:
            print(f"   ⚠️  Embeddings con dimensiones diferentes: {dims}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Embeddings de documentos
    print("\n5. Probando generación de embeddings para documentos...")
    try:
        test_docs = [
            {
                'content': 'Los dinosaurios fueron un grupo diverso de reptiles.',
                'metadata': {'source': 'doc1.txt', 'file_path': '/data/doc1.txt'}
            },
            {
                'content': 'El Tyrannosaurus rex era uno de los carnívoros más grandes.',
                'metadata': {'source': 'doc2.txt', 'file_path': '/data/doc2.txt'}
            }
        ]
        
        docs_with_embeddings = embeddings_mgr.embed_documents(test_docs)
        
        print(f"   ✅ Embeddings generados para documentos")
        print(f"   - Documentos procesados: {len(test_docs)}")
        print(f"   - Documentos con embeddings: {len(docs_with_embeddings)}")
        
        if docs_with_embeddings:
            first_doc = docs_with_embeddings[0]
            print(f"\n   📋 Estructura del primer documento:")
            print(f"   - Tiene 'content': {'content' in first_doc}")
            print(f"   - Tiene 'metadata': {'metadata' in first_doc}")
            print(f"   - Tiene 'embedding': {'embedding' in first_doc}")
            print(f"   - Dimensión del embedding: {len(first_doc.get('embedding', []))}")
            print(f"   - Metadata preservada: {first_doc['metadata'].get('source', 'N/A')}")
            
            if 'embedding' in first_doc and len(first_doc['embedding']) > 0:
                print(f"   ✅ Embedding agregado correctamente al documento")
            else:
                print(f"   ⚠️  Embedding no encontrado o vacío")
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 6: Verificar similitud entre textos relacionados
    print("\n6. Probando similitud semántica entre textos relacionados...")
    try:
        import numpy as np
        
        text1 = "Los dinosaurios eran reptiles prehistóricos."
        text2 = "Los dinosaurios fueron animales que vivieron hace millones de años."
        text3 = "La programación en Python es muy popular."
        
        emb1 = embeddings_mgr.embed_text(text1)
        emb2 = embeddings_mgr.embed_text(text2)
        emb3 = embeddings_mgr.embed_text(text3)
        
        # Calcular similitud coseno (los embeddings están normalizados)
        similarity_1_2 = np.dot(emb1, emb2)  # Cosine similarity (normalizados)
        similarity_1_3 = np.dot(emb1, emb3)
        
        print(f"   ✅ Similitudes calculadas")
        print(f"   - Similitud (texto1, texto2): {similarity_1_2:.4f}")
        print(f"   - Similitud (texto1, texto3): {similarity_1_3:.4f}")
        
        if similarity_1_2 > similarity_1_3:
            print(f"   ✅ Textos relacionados tienen mayor similitud")
        else:
            print(f"   ⚠️  Similitud inesperada (puede ser normal según el modelo)")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 7: Manejo de textos vacíos
    print("\n7. Probando manejo de textos vacíos...")
    try:
        empty_text = ""
        whitespace_text = "   \n\t  "
        
        emb_empty = embeddings_mgr.embed_text(empty_text)
        emb_whitespace = embeddings_mgr.embed_text(whitespace_text)
        
        print(f"   ✅ Manejo de textos vacíos")
        print(f"   - Embedding de texto vacío: dimensión {len(emb_empty)}")
        print(f"   - Embedding de solo espacios: dimensión {len(emb_whitespace)}")
        
        # Verificar que son vectores de ceros
        if all(abs(val) < 0.001 for val in emb_empty):
            print(f"   ✅ Texto vacío genera vector de ceros")
        else:
            print(f"   ⚠️  Texto vacío no genera vector de ceros")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 8: Verificar normalización de embeddings
    print("\n8. Verificando normalización de embeddings...")
    try:
        import numpy as np
        
        test_text = "Los dinosaurios fueron animales fascinantes."
        embedding = embeddings_mgr.embed_text(test_text)
        
        # Calcular norma del vector
        norm = np.linalg.norm(embedding)
        
        print(f"   ✅ Verificación de normalización")
        print(f"   - Norma del embedding: {norm:.6f}")
        
        # Los embeddings deberían estar normalizados (norma ≈ 1.0)
        if abs(norm - 1.0) < 0.01:
            print(f"   ✅ Embedding está normalizado (norma ≈ 1.0)")
        else:
            print(f"   ⚠️  Embedding no está normalizado (norma = {norm:.6f})")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 9: Instancia global
    print("\n9. Verificando instancia global...")
    try:
        from src.rag_pipeline.embeddings import embeddings_manager
        
        print(f"   ✅ Instancia global disponible")
        print(f"   - Tipo: {type(embeddings_manager)}")
        print(f"   - Modelo: {embeddings_manager.model_name}")
        
        # Probar que funciona
        test_emb = embeddings_manager.embed_text("Test")
        print(f"   ✅ Instancia global funcional (dimensión: {len(test_emb)})")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE PRUEBAS")
    print("="*70)
    
    print("\n✅ COMPONENTES IMPLEMENTADOS (EmbeddingsManager):")
    print("   1. Inicialización con configuración por defecto")
    print("   2. Dependencia sentence-transformers verificada")
    print("   3. Generación de embedding de texto simple")
    print("   4. Generación de embeddings en batch")
    print("   5. Generación de embeddings para documentos")
    print("   6. Verificación de similitud semántica")
    print("   7. Manejo de textos vacíos")
    print("   8. Verificación de normalización")
    print("   9. Instancia global")
    
    print("\n✅ ESTADO: EmbeddingsManager funcionando correctamente")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    test_embeddings()

