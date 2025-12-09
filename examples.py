"""
Script de ejemplo para demostración del sistema.
"""
import os
from pathlib import Path

# Asegurarse de que las variables de entorno estén configuradas
os.environ['GOOGLE_API_KEY'] = 'your-key-here'  # Cambiar
os.environ['GROQ_API_KEY'] = 'your-key-here'     # Cambiar

from src.agents.autonomous_orchestrator import AutonomousOrchestrator
from src.agents.autonomous_indexer_agent import AutonomousIndexerAgent
from src.rag_pipeline.pipelines import RAGPipeline
from src.tools.trace_exporter import TraceExporterTool


def example_1_basic_query():
    """Ejemplo 1: Consulta básica de búsqueda con Sistema Autónomo."""
    print("\n" + "="*60)
    print("EJEMPLO 1: Consulta de Búsqueda (Sistema Autónomo)")
    print("="*60)
    
    orchestrator = AutonomousOrchestrator()
    
    query = "¿Qué es la diabetes y cuáles son sus síntomas principales?"
    
    print(f"\n📝 Consulta: {query}\n")
    
    result = orchestrator.process_query(query)
    
    print("🤖 Respuesta:")
    print(result['response'])
    print("\n" + "-"*60)
    print(f"📊 Intención detectada: {result.get('classification', {}).get('intent', 'N/A')}")
    print(f"📚 Documentos consultados: {result.get('documents_found', 0)}")
    print(f"🔄 Regeneraciones: {result.get('regeneration_count', 0)}")
    print(f"🤖 Agentes llamados: {', '.join(result.get('trace', {}).get('agents_called', []))}")


def example_2_summary():
    """Ejemplo 2: Solicitud de resumen con Sistema Autónomo."""
    print("\n" + "="*60)
    print("EJEMPLO 2: Solicitud de Resumen (Sistema Autónomo)")
    print("="*60)
    
    orchestrator = AutonomousOrchestrator()
    
    query = "Resume los principales tratamientos para la hipertensión"
    
    print(f"\n📝 Consulta: {query}\n")
    
    result = orchestrator.process_query(query)
    
    print("🤖 Respuesta:")
    print(result['response'])
    print("\n" + "-"*60)
    print(f"🔧 Herramientas usadas: {', '.join(result.get('trace', {}).get('tools_used', []))}")


def example_3_comparison():
    """Ejemplo 3: Comparación de conceptos con Sistema Autónomo."""
    print("\n" + "="*60)
    print("EJEMPLO 3: Comparación (Sistema Autónomo)")
    print("="*60)
    
    orchestrator = AutonomousOrchestrator()
    
    query = "Compara diabetes tipo 1 y diabetes tipo 2"
    
    print(f"\n📝 Consulta: {query}\n")
    
    result = orchestrator.process_query(query)
    
    print("🤖 Respuesta:")
    print(result['response'])
    print("\n" + "-"*60)
    print(f"✅ Validación: {result.get('validation', {}).get('is_valid', 'N/A')}")


def example_4_general():
    """Ejemplo 4: Consulta general (sin RAG) con Sistema Autónomo."""
    print("\n" + "="*60)
    print("EJEMPLO 4: Consulta General (Sistema Autónomo)")
    print("="*60)
    
    orchestrator = AutonomousOrchestrator()
    
    query = "¿Cuál es la capital de Francia?"
    
    print(f"\n📝 Consulta: {query}\n")
    
    result = orchestrator.process_query(query)
    
    print("🤖 Respuesta:")
    print(result['response'])
    print("\n" + "-"*60)
    print(f"📊 Requiere RAG: {result.get('classification', {}).get('requires_rag', False)}")
    print(f"🤖 Decisión autónoma: Respuesta general sin documentos")


def example_5_batch_processing():
    """Ejemplo 5: Procesamiento en lote con Sistema Autónomo."""
    print("\n" + "="*60)
    print("EJEMPLO 5: Procesamiento en Lote (Sistema Autónomo)")
    print("="*60)
    
    orchestrator = AutonomousOrchestrator()
    
    queries = [
        "¿Qué es la hipertensión?",
        "Resume los síntomas del asma",
        "Compara paracetamol e ibuprofeno"
    ]
    
    print(f"\n📋 Procesando {len(queries)} consultas con agentes autónomos...\n")
    
    results = []
    for query in queries:
        result = orchestrator.process_query(query)
        results.append(result)
    
    for i, result in enumerate(results, 1):
        print(f"\n--- Consulta {i} ---")
        print(f"Query: {queries[i-1]}")
        print(f"Intent: {result.get('classification', {}).get('intent', 'N/A')}")
        print(f"Docs: {result.get('documents_found', 0)}")
        print(f"Tools: {', '.join(result.get('trace', {}).get('tools_used', [])[:3])}...")


def example_6_with_tracing():
    """Ejemplo 6: Consulta con análisis de traza autónoma."""
    print("\n" + "="*60)
    print("EJEMPLO 6: Análisis de Traza de Ejecución (Autónomo)")
    print("="*60)
    
    orchestrator = AutonomousOrchestrator()
    
    query = "¿Cuáles son los factores de riesgo cardiovascular?"
    
    print(f"\n📝 Consulta: {query}\n")
    
    result = orchestrator.process_query(query)
    
    print("🤖 Respuesta:")
    print(result['response'])
    
    # Mostrar traza detallada
    if result.get('trace'):
        trace = result['trace']
        print("\n" + "-"*60)
        print("📊 TRAZA DE EJECUCIÓN AUTÓNOMA:")
        print("-"*60)
        print(f"Agentes llamados: {', '.join(trace.get('agents_called', []))}")
        print(f"Tools usadas: {', '.join(trace.get('tools_used', []))}")
        print(f"Regeneraciones: {trace.get('regeneration_count', 0)}")
        print(f"Total de pasos: {len(trace.get('steps', []))}")


def example_7_export_case_study():
    """Ejemplo 7: Exportar caso de uso con Sistema Autónomo."""
    print("\n" + "="*60)
    print("EJEMPLO 7: Exportar Caso de Uso (Sistema Autónomo)")
    print("="*60)
    
    orchestrator = AutonomousOrchestrator()
    
    query = "Explica qué es la obesidad y sus consecuencias"
    
    print(f"\n📝 Consulta: {query}\n")
    
    result = orchestrator.process_query(query)
    
    print("🤖 Respuesta generada con agentes autónomos ✓")
    
    # Exportar
    filepath = TraceExporterTool.export_case_study(
        case_number=1,
        query=query,
        response=result['response'],
        trace_data=result.get('trace', {}),
        domain="salud_autonomo"
    )
    
    print(f"\n💾 Caso de uso exportado a: {filepath}")
    print(f"🔧 Decisiones autónomas documentadas en trace")


def example_8_system_stats():
    """Ejemplo 8: Estadísticas del Sistema Autónomo."""
    print("\n" + "="*60)
    print("EJEMPLO 8: Estadísticas del Sistema Autónomo")
    print("="*60)
    
    # Indexer stats
    indexer = AutonomousIndexerAgent()
    stats_result = indexer.get_stats()
    
    print("\n🤖 Sistema Agentic AI Autónomo:")
    print(f"   - Agentes: 6 autónomos con tool calling")
    print(f"   - Total Tools: 22 (11 query + 11 indexing)")
    print(f"   - LLMs: Gemini 2.5 Flash + Groq Llama 3.1 70B")
    
    print("\n📚 Índice Vectorial:")
    if stats_result['status'] == 'success':
        print(f"   {stats_result['response']}")
    else:
        print(f"   - Error obteniendo estadísticas")
    
    print("\n✨ Características Autónomas:")
    print("   - Agentes deciden qué tools usar")
    print("   - Sin flujo hardcoded")
    print("   - Trazabilidad completa de decisiones")


def run_all_examples():
    """Ejecuta todos los ejemplos con Sistema Autónomo."""
    print("\n" + "="*60)
    print("🚀 SISTEMA AGENTIC AI AUTÓNOMO - DEMOSTRACIÓN COMPLETA")
    print("="*60)
    
    try:
        # Cargar índice con agente autónomo
        print("\n📚 Cargando índice con Agente Indexador Autónomo...")
        indexer = AutonomousIndexerAgent()
        indexer.load_existing_index()
        print("✅ Índice cargado por agente autónomo\n")
        
        # Ejecutar ejemplos
        example_1_basic_query()
        example_2_summary()
        example_3_comparison()
        example_4_general()
        example_5_batch_processing()
        example_6_with_tracing()
        example_7_export_case_study()
        example_8_system_stats()
        
        print("\n" + "="*60)
        print("✅ DEMOSTRACIÓN AUTÓNOMA COMPLETADA")
        print("="*60)
        print("\n🎯 Sistema Autónomo Demostrado:")
        print("   ✓ 6 Agentes autónomos con tool calling")
        print("   ✓ 22 LangChain tools (@tool decorator)")
        print("   ✓ Decisiones autónomas documentadas")
        print("   ✓ Trazabilidad completa de herramientas")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\n💡 Asegúrate de:")
        print("   1. Tener documentos en data/raw/")
        print("   2. Haber ejecutado: python main.py --index")
        print("   3. Configurar API keys en .env")
        print("   4. Sistema autónomo inicializado correctamente\n")


if __name__ == "__main__":
    # Ejecutar un ejemplo específico o todos
    import sys
    
    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        
        examples = {
            '1': example_1_basic_query,
            '2': example_2_summary,
            '3': example_3_comparison,
            '4': example_4_general,
            '5': example_5_batch_processing,
            '6': example_6_with_tracing,
            '7': example_7_export_case_study,
            '8': example_8_system_stats
        }
        
        if example_num in examples:
            # Cargar índice con agente autónomo
            indexer = AutonomousIndexerAgent()
            indexer.load_existing_index()
            
            examples[example_num]()
        else:
            print(f"Ejemplo {example_num} no encontrado")
            print("Ejemplos disponibles: 1-8")
    else:
        run_all_examples()
