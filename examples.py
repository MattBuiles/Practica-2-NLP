"""
Script de ejemplo para demostración del sistema.
"""
import os
from pathlib import Path

# Asegurarse de que las variables de entorno estén configuradas
os.environ['GOOGLE_API_KEY'] = 'your-key-here'  # Cambiar
os.environ['GROQ_API_KEY'] = 'your-key-here'     # Cambiar

from src.agents.orchestrator import Orchestrator
from src.rag_pipeline.pipelines import RAGPipeline
from src.tools.trace_exporter import TraceExporterTool


def example_1_basic_query():
    """Ejemplo 1: Consulta básica de búsqueda."""
    print("\n" + "="*60)
    print("EJEMPLO 1: Consulta de Búsqueda")
    print("="*60)
    
    orchestrator = Orchestrator()
    
    query = "¿Qué es la diabetes y cuáles son sus síntomas principales?"
    
    print(f"\n📝 Consulta: {query}\n")
    
    result = orchestrator.process_query(query)
    
    print("🤖 Respuesta:")
    print(result['response'])
    print("\n" + "-"*60)
    print(f"📊 Intención detectada: {result['intent']}")
    print(f"📚 Documentos consultados: {result.get('documents_found', 0)}")
    print(f"🔄 Regeneraciones: {result.get('regeneration_attempts', 0)}")


def example_2_summary():
    """Ejemplo 2: Solicitud de resumen."""
    print("\n" + "="*60)
    print("EJEMPLO 2: Solicitud de Resumen")
    print("="*60)
    
    orchestrator = Orchestrator()
    
    query = "Resume los principales tratamientos para la hipertensión"
    
    print(f"\n📝 Consulta: {query}\n")
    
    result = orchestrator.process_query(query)
    
    print("🤖 Respuesta:")
    print(result['response'])


def example_3_comparison():
    """Ejemplo 3: Comparación de conceptos."""
    print("\n" + "="*60)
    print("EJEMPLO 3: Comparación")
    print("="*60)
    
    orchestrator = Orchestrator()
    
    query = "Compara diabetes tipo 1 y diabetes tipo 2"
    
    print(f"\n📝 Consulta: {query}\n")
    
    result = orchestrator.process_query(query)
    
    print("🤖 Respuesta:")
    print(result['response'])


def example_4_general():
    """Ejemplo 4: Consulta general (sin RAG)."""
    print("\n" + "="*60)
    print("EJEMPLO 4: Consulta General")
    print("="*60)
    
    orchestrator = Orchestrator()
    
    query = "¿Cuál es la capital de Francia?"
    
    print(f"\n📝 Consulta: {query}\n")
    
    result = orchestrator.process_query(query)
    
    print("🤖 Respuesta:")
    print(result['response'])
    print("\n" + "-"*60)
    print(f"📊 Requiere RAG: {result.get('requires_rag', False)}")


def example_5_batch_processing():
    """Ejemplo 5: Procesamiento en lote."""
    print("\n" + "="*60)
    print("EJEMPLO 5: Procesamiento en Lote")
    print("="*60)
    
    orchestrator = Orchestrator()
    
    queries = [
        "¿Qué es la hipertensión?",
        "Resume los síntomas del asma",
        "Compara paracetamol e ibuprofeno"
    ]
    
    print(f"\n📋 Procesando {len(queries)} consultas...\n")
    
    results = orchestrator.process_batch(queries)
    
    for i, result in enumerate(results, 1):
        print(f"\n--- Consulta {i} ---")
        print(f"Query: {queries[i-1]}")
        print(f"Intent: {result['intent']}")
        print(f"Docs: {result.get('documents_found', 0)}")


def example_6_with_tracing():
    """Ejemplo 6: Consulta con análisis de traza."""
    print("\n" + "="*60)
    print("EJEMPLO 6: Análisis de Traza de Ejecución")
    print("="*60)
    
    orchestrator = Orchestrator()
    
    query = "¿Cuáles son los factores de riesgo cardiovascular?"
    
    print(f"\n📝 Consulta: {query}\n")
    
    result = orchestrator.process_query(query, include_trace=True)
    
    print("🤖 Respuesta:")
    print(result['response'])
    
    # Mostrar traza
    if result.get('trace_summary'):
        print("\n" + "-"*60)
        print("📊 TRAZA DE EJECUCIÓN:")
        print("-"*60)
        print(result['trace_summary'])


def example_7_export_case_study():
    """Ejemplo 7: Exportar caso de uso."""
    print("\n" + "="*60)
    print("EJEMPLO 7: Exportar Caso de Uso")
    print("="*60)
    
    orchestrator = Orchestrator()
    
    query = "Explica qué es la obesidad y sus consecuencias"
    
    print(f"\n📝 Consulta: {query}\n")
    
    result = orchestrator.process_query(query, include_trace=True)
    
    print("🤖 Respuesta generada ✓")
    
    # Exportar
    filepath = TraceExporterTool.export_case_study(
        case_number=1,
        query=query,
        response=result['response'],
        trace_data=result.get('trace', {}),
        domain="salud"
    )
    
    print(f"\n💾 Caso de uso exportado a: {filepath}")


def example_8_system_stats():
    """Ejemplo 8: Estadísticas del sistema."""
    print("\n" + "="*60)
    print("EJEMPLO 8: Estadísticas del Sistema")
    print("="*60)
    
    orchestrator = Orchestrator()
    
    stats = orchestrator.get_system_stats()
    
    print("\n📊 Configuración de Agentes:")
    for agent, llm in stats['agents'].items():
        print(f"   - {agent}: {llm}")
    
    print(f"\n📚 Vector Store:")
    vs_stats = stats['vectorstore']
    print(f"   - Status: {vs_stats.get('status', 'unknown')}")
    print(f"   - Documentos: {vs_stats.get('total_documents', 0)}")
    
    print(f"\n📝 Trazas recolectadas: {stats['traces_collected']}")


def run_all_examples():
    """Ejecuta todos los ejemplos."""
    print("\n" + "="*60)
    print("🚀 SISTEMA AGENTIC AI - DEMOSTRACIÓN COMPLETA")
    print("="*60)
    
    try:
        # Cargar índice primero
        print("\n📚 Cargando índice de documentos...")
        pipeline = RAGPipeline()
        pipeline.load_existing_index()
        print("✅ Índice cargado\n")
        
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
        print("✅ DEMOSTRACIÓN COMPLETADA")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\n💡 Asegúrate de:")
        print("   1. Tener documentos en data/raw/")
        print("   2. Haber ejecutado: python main.py --index")
        print("   3. Configurar API keys en .env\n")


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
            # Cargar índice
            pipeline = RAGPipeline()
            pipeline.load_existing_index()
            
            examples[example_num]()
        else:
            print(f"Ejemplo {example_num} no encontrado")
            print("Ejemplos disponibles: 1-8")
    else:
        run_all_examples()
