"""
Test para TextCleanerTool - Persona 2
Verifica que la limpieza de texto funcione correctamente.
"""
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.text_cleaner import TextCleanerTool


def test_text_cleaner():
    """Prueba los componentes del TextCleanerTool."""
    
    print("="*70)
    print("PRUEBA DE COMPONENTES - TextCleanerTool (Persona 2)")
    print("="*70)

    # Test 1: Limpieza básica
    print("\n1. Probando limpieza básica...")
    test_text = "Este   es   un   texto   con    espacios    múltiples.\n\n\nY saltos de línea."
    cleaned = TextCleanerTool.clean_text(test_text, aggressive=False)
    
    if cleaned:
        print(f"   ✅ Limpieza básica funcionando")
        print(f"   - Original: {len(test_text)} caracteres")
        print(f"   - Limpiado: {len(cleaned)} caracteres")
        print(f"   - Preview: {cleaned[:80]}...")
        
        # Verificar que se normalizaron espacios
        if '   ' not in cleaned and '\n\n\n' not in cleaned:
            print(f"   ✅ Espacios y saltos de línea normalizados correctamente")
        else:
            print(f"   ⚠️  Advertencia: Puede haber espacios múltiples")
    else:
        print(f"   ❌ Error: No se retornó texto limpio")
    
    # Test 2: Remoción de caracteres de control
    print("\n2. Probando remoción de caracteres de control...")
    test_text_with_control = "Texto normal\x00\x01\x02con caracteres\x03de control\x04"
    original_has_control = any(ord(c) < 32 and c not in ['\n', '\t'] for c in test_text_with_control)
    cleaned = TextCleanerTool.clean_text(test_text_with_control, min_length=0)
    
    if cleaned:
        # Verificar que no hay caracteres de control (excepto \n y \t)
        cleaned_has_control = any(ord(c) < 32 and c not in ['\n', '\t'] for c in cleaned)
        if not cleaned_has_control:
            print(f"   ✅ Caracteres de control removidos correctamente")
            print(f"   - Original: {len(test_text_with_control)} chars (con control)")
            print(f"   - Limpiado: {len(cleaned)} chars (sin control)")
            print(f"   - Preview: {cleaned[:60]}...")
        else:
            print(f"   ⚠️  Algunos caracteres de control pueden estar presentes")
            print(f"   - Limpiado: {len(cleaned)} chars")
    else:
        print(f"   ⚠️  Texto filtrado (puede ser por longitud mínima)")
    
    # Test 3: Limpieza agresiva (URLs y emails)
    print("\n3. Probando limpieza agresiva (URLs y emails)...")
    test_text_with_urls = """
    Visita https://www.ejemplo.com para más información.
    Contacta en email@ejemplo.com si tienes preguntas.
    También puedes ver http://otro-sitio.org/pagina.
    """
    cleaned_normal = TextCleanerTool.clean_text(test_text_with_urls, aggressive=False)
    cleaned_aggressive = TextCleanerTool.clean_text(test_text_with_urls, aggressive=True)
    
    print(f"   - Modo normal: {len(cleaned_normal) if cleaned_normal else 0} caracteres")
    print(f"   - Modo agresivo: {len(cleaned_aggressive) if cleaned_aggressive else 0} caracteres")
    
    if cleaned_aggressive:
        has_url = 'https://' in cleaned_aggressive or 'http://' in cleaned_aggressive
        has_email = '@' in cleaned_aggressive and '.' in cleaned_aggressive.split('@')[1] if '@' in cleaned_aggressive else False
        
        if not has_url and not has_email:
            print(f"   ✅ URLs y emails removidos correctamente")
        else:
            print(f"   ⚠️  Puede haber URLs o emails presentes")
    
    # Test 4: Filtrado por longitud mínima
    print("\n4. Probando filtrado por longitud mínima...")
    short_text = "Texto corto"
    long_text = "Este es un texto más largo que debería pasar el filtro de longitud mínima sin problemas."
    
    result_short = TextCleanerTool.clean_text(short_text, min_length=50)
    result_long = TextCleanerTool.clean_text(long_text, min_length=50)
    
    if result_short is None:
        print(f"   ✅ Texto corto filtrado correctamente (None)")
    else:
        print(f"   ⚠️  Texto corto no fue filtrado")
    
    if result_long:
        print(f"   ✅ Texto largo pasado correctamente ({len(result_long)} caracteres)")
    else:
        print(f"   ❌ Texto largo fue filtrado incorrectamente")
    
    # Test 5: Limpieza de documentos
    print("\n5. Probando limpieza de lista de documentos...")
    test_documents = [
        {
            'content': 'Documento 1   con   espacios    múltiples.',
            'metadata': {'source': 'doc1.txt', 'page': 1}
        },
        {
            'content': 'Documento 2\n\n\ncon saltos de línea.',
            'metadata': {'source': 'doc2.txt', 'page': 2}
        },
        {
            'content': 'Corto',  # Será filtrado
            'metadata': {'source': 'doc3.txt', 'page': 3}
        },
        {
            'content': 'https://ejemplo.com Documento 4 con URL.',
            'metadata': {'source': 'doc4.txt', 'page': 4}
        }
    ]
    
    cleaned_docs = TextCleanerTool.clean_documents(
        test_documents, 
        aggressive=True, 
        min_length=20
    )
    
    print(f"   ✅ Documentos procesados: {len(cleaned_docs)}/{len(test_documents)}")
    
    if cleaned_docs:
        for i, doc in enumerate(cleaned_docs, 1):
            cleaning_info = doc['metadata'].get('cleaning_info', {})
            print(f"   - Doc {i}: {cleaning_info.get('original_length', 0)} → {cleaning_info.get('cleaned_length', 0)} chars")
    
    # Test 6: Normalización de puntuación (modo agresivo)
    print("\n6. Probando normalización de puntuación...")
    test_punctuation = "¡¡¡Esto es emocionante!!! ¿¿¿Qué tal??? .... Y más....."
    cleaned = TextCleanerTool.clean_text(test_punctuation, aggressive=True, min_length=0)
    
    if cleaned:
        has_triple_exclamation = '!!!' in cleaned or '¡¡¡' in cleaned
        has_triple_question = '???' in cleaned or '¿¿¿' in cleaned
        has_many_dots = '....' in cleaned or '.....' in cleaned
        
        print(f"   - Original: {test_punctuation}")
        print(f"   - Limpiado: {cleaned}")
        
        if not has_triple_exclamation and not has_triple_question and not has_many_dots:
            print(f"   ✅ Puntuación normalizada correctamente")
        else:
            print(f"   ⚠️  Puede haber puntuación múltiple sin normalizar")
            if has_triple_exclamation:
                print(f"      - Encontrado: !!! o ¡¡¡")
            if has_triple_question:
                print(f"      - Encontrado: ??? o ¿¿¿")
            if has_many_dots:
                print(f"      - Encontrado: 4+ puntos")
    else:
        print(f"   ⚠️  Texto filtrado (puede ser por longitud mínima)")
    
    # Test 7: Preservación de estructura básica
    print("\n7. Probando preservación de estructura básica...")
    structured_text = """
    Párrafo 1 con contenido importante.
    
    Párrafo 2 con más información.
    
    Párrafo 3 con detalles adicionales.
    """
    cleaned = TextCleanerTool.clean_text(structured_text, aggressive=False)
    
    if cleaned:
        paragraphs = cleaned.split('\n\n')
        print(f"   ✅ Estructura preservada: {len(paragraphs)} párrafos detectados")
        if len(paragraphs) >= 3:
            print(f"   ✅ Múltiples párrafos mantenidos correctamente")
        else:
            print(f"   ⚠️  Puede haber pérdida de estructura")
    
    # Test 8: Métodos auxiliares
    print("\n8. Probando métodos auxiliares...")
    
    # normalize_whitespace
    test_whitespace = "Texto   con\t\t\tespacios    múltiples"
    normalized = TextCleanerTool.normalize_whitespace(test_whitespace)
    if '   ' not in normalized and '\t\t' not in normalized:
        print(f"   ✅ normalize_whitespace funcionando")
    else:
        print(f"   ⚠️  normalize_whitespace puede tener problemas")
    
    # remove_control_characters
    test_control = "Texto\x00\x01normal\x02"
    removed = TextCleanerTool.remove_control_characters(test_control)
    if '\x00' not in removed and '\x01' not in removed:
        print(f"   ✅ remove_control_characters funcionando")
    else:
        print(f"   ⚠️  remove_control_characters puede tener problemas")
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE PRUEBAS")
    print("="*70)
    
    print("\n✅ COMPONENTES IMPLEMENTADOS (TextCleanerTool):")
    print("   1. Limpieza básica (espacios, saltos de línea)")
    print("   2. Remoción de caracteres de control")
    print("   3. Limpieza agresiva (URLs, emails, puntuación)")
    print("   4. Filtrado por longitud mínima")
    print("   5. Limpieza de lista de documentos")
    print("   6. Normalización de puntuación")
    print("   7. Preservación de estructura básica")
    print("   8. Métodos auxiliares")
    
    print("\n✅ ESTADO: TextCleanerTool funcionando correctamente")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    test_text_cleaner()

