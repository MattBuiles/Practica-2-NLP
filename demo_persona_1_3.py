"""
Script de prueba para demostrar la funcionalidad de Persona 1 y Persona 3.

Este script simula el funcionamiento completo del sistema usando datos mock
para el vector store (que implementará Persona 2).

Demuestra:
- Clasificación de intención (Persona 1)
- Recuperación semántica (Persona 3)
- Generación RAG (Persona 3)
- Validación con ciclo de regeneración (Persona 3)
- Orquestación completa (Persona 1)
"""

import os
import sys
from typing import List, Dict, Any

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 80)
print("DEMO: Sistema Agentic AI - Persona 1 + Persona 3")
print("=" * 80)
print()

# ============================================================================
# PASO 1: MOCK del VectorStore (simula lo que hará Persona 2)
# ============================================================================

class MockVectorStoreManager:
    """
    Mock del VectorStoreManager que simula FAISS.
    En producción, Persona 2 implementará esto con FAISS real.
    """
    
    def __init__(self):
        # Documentos mock sobre COVID-19
        self.mock_documents = [
            {
                'content': 'El COVID-19 es una enfermedad respiratoria causada por el virus SARS-CoV-2. '
                          'Se transmite principalmente a través de gotículas respiratorias cuando una persona '
                          'infectada tose, estornuda o habla. El periodo de incubación es de 2 a 14 días.',
                'metadata': {'source': 'covid_general.pdf', 'chunk_index': 0},
                'score': 0.95
            },
            {
                'content': 'Los síntomas más comunes del COVID-19 incluyen fiebre (38°C o más), tos seca '
                          'persistente, fatiga extrema y dificultad para respirar. Otros síntomas pueden incluir '
                          'pérdida del olfato o gusto, dolor de cabeza y dolor muscular.',
                'metadata': {'source': 'sintomas_covid.pdf', 'chunk_index': 0},
                'score': 0.92
            },
            {
                'content': 'La prevención del COVID-19 incluye el uso de mascarillas en espacios cerrados, '
                          'mantener distancia física de al menos 1.5 metros, lavado frecuente de manos con '
                          'agua y jabón por 20 segundos, y la vacunación completa.',
                'metadata': {'source': 'prevencion_covid.html', 'chunk_index': 0},
                'score': 0.88
            },
            {
                'content': 'Las vacunas contra el COVID-19 han demostrado ser seguras y efectivas. '
                          'La mayoría requiere dos dosis para protección completa. La eficacia general '
                          'ronda el 90-95% contra enfermedad grave.',
                'metadata': {'source': 'vacunas_covid.pdf', 'chunk_index': 1},
                'score': 0.85
            },
            {
                'content': 'El tratamiento del COVID-19 depende de la gravedad. Los casos leves pueden '
                          'tratarse en casa con reposo, hidratación y medicamentos para controlar síntomas. '
                          'Los casos graves requieren hospitalización y pueden necesitar oxígeno suplementario.',
                'metadata': {'source': 'tratamiento_covid.pdf', 'chunk_index': 0},
                'score': 0.82
            }
        ]
        print("[MOCK] VectorStoreManager inicializado con documentos mock de COVID-19")
    
    def similarity_search(self, query: str, k: int = 5, 
                         score_threshold: float = None) -> List[Dict[str, Any]]:
        """Simula búsqueda en FAISS."""
        print(f"[MOCK] Búsqueda: '{query[:50]}...' (k={k}, threshold={score_threshold})")
        
        # Retornar top k documentos
        results = self.mock_documents[:k]
        
        # Filtrar por threshold si existe
        if score_threshold:
            results = [doc for doc in results if doc['score'] >= score_threshold]
        
        print(f"[MOCK] Retornando {len(results)} documentos")
        return results

# Reemplazar el vectorstore_manager global con el mock
from src.rag_pipeline import vectorstore
vectorstore.vectorstore_manager = MockVectorStoreManager()

# ============================================================================
# PASO 2: Importar componentes de Persona 1 y Persona 3
# ============================================================================

print("\n" + "=" * 80)
print("Importando componentes implementados...")
print("=" * 80)

try:
    # Persona 1
    from src.agents.classifier_agent import ClassifierAgent
    from src.agents.orchestrator import Orchestrator
    print("✓ ClassifierAgent (Persona 1) importado")
    print("✓ Orchestrator (Persona 1) importado")
    
    # Persona 3
    from src.agents.retriever_agent import RetrieverAgent
    from src.agents.rag_agent import RAGAgent
    from src.agents.critic_agent import CriticAgent
    print("✓ RetrieverAgent (Persona 3) importado")
    print("✓ RAGAgent (Persona 3) importado")
    print("✓ CriticAgent (Persona 3) importado")
    
except ImportError as e:
    print(f"\n❌ Error de importación: {e}")
    print("\nAsegúrate de que las dependencias estén instaladas:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# ============================================================================
# PASO 3: Pruebas individuales de cada componente
# ============================================================================

print("\n" + "=" * 80)
print("PRUEBA 1: ClassifierAgent (Persona 1)")
print("=" * 80)

classifier = ClassifierAgent()
query_test = "¿Cuáles son los síntomas del COVID-19?"

print(f"\nQuery: {query_test}")
print("\nClasificando intención...")

classification = classifier.classify(query_test)

print(f"\nResultado:")
print(f"  Intención: {classification['intent']}")
print(f"  Confianza: {classification['confidence']:.2f}")
print(f"  Requiere RAG: {classification['requires_rag']}")
print(f"  Razonamiento: {classification['reasoning'][:100]}...")

# ============================================================================

print("\n" + "=" * 80)
print("PRUEBA 2: RetrieverAgent (Persona 3)")
print("=" * 80)

retriever = RetrieverAgent()

print(f"\nRecuperando documentos para: '{query_test}'")
print("Optimizando query con LLM...")

documents = retriever.retrieve(
    query=query_test,
    k=3,
    optimize=True,
    intent="busqueda",
    score_threshold=0.5
)

print(f"\nDocumentos recuperados: {len(documents)}")
for i, doc in enumerate(documents, 1):
    print(f"\n  Doc {i}:")
    print(f"    Score: {doc['score']:.2f}")
    print(f"    Fuente: {doc['metadata']['source']}")
    print(f"    Contenido: {doc['content'][:100]}...")

# ============================================================================

print("\n" + "=" * 80)
print("PRUEBA 3: RAGAgent (Persona 3)")
print("=" * 80)

rag_agent = RAGAgent()

print(f"\nGenerando respuesta con {len(documents)} documentos...")
print("Usando prompt especializado de BÚSQUEDA...")

response_data = rag_agent.generate_response(
    query=query_test,
    documents=documents,
    intent="busqueda"
)

print(f"\nRespuesta generada:")
print(response_data['response'])

print(f"\nFuentes utilizadas: {len(response_data['sources'])}")
for source in response_data['sources']:
    print(f"  - {source['id']}: {source['source']}")

# ============================================================================

print("\n" + "=" * 80)
print("PRUEBA 4: CriticAgent (Persona 3)")
print("=" * 80)

critic = CriticAgent()

print("\nValidando respuesta con 5 criterios...")
print("(Coherencia, Alineación, Alucinaciones, Completitud, Citas)")

validation = critic.validate(
    query=query_test,
    response=response_data['response'],
    context_docs=documents
)

print(f"\nResultado de validación:")
print(f"  Score global: {validation['overall_score']:.3f}")
print(f"  Es válida: {validation['is_valid']}")
print(f"  Necesita regeneración: {validation['needs_regeneration']}")

print(f"\nScores por criterio:")
for criterio, score in validation['criteria_scores'].items():
    print(f"  {criterio.capitalize()}: {score:.2f}")

if validation['issues']:
    print(f"\nProblemas detectados:")
    for issue in validation['issues']:
        print(f"  - {issue}")

# ============================================================================

print("\n" + "=" * 80)
print("PRUEBA 5: Ciclo de Regeneración (Persona 3)")
print("=" * 80)

print("\nProbando validación con ciclo de regeneración...")
print("Máximo 2 intentos si la respuesta no es suficiente")

def regenerate_callback(query, docs, intent):
    """Callback para regenerar respuesta."""
    print("\n  [REGENERANDO] Nueva respuesta solicitada...")
    return rag_agent.generate_response(query, docs, intent)

validation_result = critic.validate_with_regeneration(
    query=query_test,
    response=response_data['response'],
    context_docs=documents,
    regenerate_callback=regenerate_callback,
    max_attempts=2
)

print(f"\nResultado del ciclo:")
print(f"  Status: {validation_result['status']}")
print(f"  Intentos realizados: {validation_result['attempts']}")
print(f"  Score final: {validation_result['validation']['overall_score']:.3f}")

print(f"\nRespuesta final:")
print(validation_result['final_response'][:200] + "...")

# ============================================================================

print("\n" + "=" * 80)
print("PRUEBA 6: Orchestrator - Flujo Completo (Persona 1)")
print("=" * 80)

orchestrator = Orchestrator()

print("\nProcesando query completa a través del orquestador...")
print("(Clasificar → Decidir Estrategia → Recuperar → Generar → Validar)")

# Query de búsqueda
print("\n--- CASO 1: Búsqueda de información ---")
result1 = orchestrator.process_query(
    query="¿Cuáles son los síntomas del COVID-19?",
    include_trace=True
)

print(f"\nIntención: {result1['intent']}")
print(f"Estrategia: {result1['strategy']}")
print(f"Documentos: {result1.get('documents_found', 0)}")
print(f"Regeneraciones: {result1.get('regeneration_attempts', 0)}")
if 'validation' in result1:
    print(f"Score validación: {result1['validation'].get('overall_score', 'N/A')}")
print(f"\nRespuesta:")
print(result1['response'][:300] + "...")

# Query general (sin RAG)
print("\n--- CASO 2: Consulta general (sin RAG) ---")
result2 = orchestrator.process_query(
    query="Hola, ¿cómo estás?",
    include_trace=True
)

print(f"\nIntención: {result2['intent']}")
print(f"Estrategia: {result2['strategy']}")
print(f"Requiere RAG: {result2['requires_rag']}")
print(f"\nRespuesta:")
print(result2['response'])

# ============================================================================

print("\n" + "=" * 80)
print("DEMOSTRACIÓN COMPLETADA")
print("=" * 80)

print("\n✓ Todos los componentes de Persona 1 y Persona 3 funcionando correctamente")
print("\nPróximos pasos:")
print("1. Persona 2: Implementar VectorStoreManager real con FAISS")
print("2. Persona 2: Recolectar e indexar 100 documentos")
print("3. Persona 4: Crear interfaz de usuario")
print("4. Persona 4: Integrar y crear 10 casos de uso")

print("\n" + "=" * 80)
print("NOTA: Este demo usa datos mock. Una vez Persona 2 implemente")
print("      el vector store real, el sistema funcionará con documentos reales.")
print("=" * 80)
