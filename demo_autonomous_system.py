"""
Script de Demostración del Sistema Agentic AI Autónomo.
Muestra cómo los agentes usan tools de forma autónoma.
"""
import logging
import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.agents.autonomous_orchestrator import AutonomousOrchestrator

# Configurar logging para ver decisiones de agentes
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def print_separator(char="=", length=100):
    """Imprime una línea separadora."""
    print("\n" + char * length + "\n")


def print_result(result: dict):
    """Imprime los resultados de forma legible."""
    print_separator("=")
    print("📊 RESULTADO DE LA CONSULTA")
    print_separator("=")
    
    print(f"🔍 Query Original: {result['query']}")
    print(f"🎯 Intención Detectada: {result['intent']}")
    print(f"📚 Documentos Usados: {result['documents_used']}")
    print(f"⏱️ Tiempo de Ejecución: {result['execution_time']:.2f}s")
    
    print_separator("-")
    print("💬 RESPUESTA GENERADA:")
    print_separator("-")
    print(result['response'])
    
    print_separator("-")
    print("✅ VALIDACIÓN:")
    print_separator("-")
    validation = result['validation']
    print(f"  ✓ Válida: {validation.get('is_valid', 'N/A')}")
    print(f"  ✓ Score de Confianza: {validation.get('confidence_score', 0):.2f}")
    if validation.get('issues'):
        print(f"  ⚠️ Problemas: {', '.join(validation['issues'])}")
    
    print_separator("-")
    print("🔄 TRAZABILIDAD:")
    print_separator("-")
    trace = result['trace']
    print(f"  • Agentes Llamados: {', '.join(trace['agents_called'])}")
    print(f"  • Tools Usadas: {', '.join(trace.get('tools_used', ['N/A']))}")
    print(f"  • Regeneraciones: {trace.get('regeneration_count', 0)}")
    
    print(f"\n  📋 Pasos Ejecutados ({len(trace['steps'])}):")
    for step in trace['steps']:
        print(f"    {step['step']}. {step['agent']} → {step['action']}")
        if 'intermediate_steps' in step.get('result', {}):
            for istep in step['result']['intermediate_steps']:
                if 'tool' in istep or 'action' in istep:
                    tool_name = istep.get('tool', istep.get('action', 'unknown'))
                    print(f"       └─ Tool: {tool_name}")
    
    print_separator("=")


def demo_1_busqueda_simple():
    """Demo 1: Búsqueda simple de información."""
    print_separator("🎬")
    print("DEMO 1: BÚSQUEDA SIMPLE")
    print("Los agentes deciden autónomamente qué tools usar")
    print_separator("🎬")
    
    orchestrator = AutonomousOrchestrator()
    
    query = "¿Qué es un dinosaurio?"
    
    print(f"\n🔎 Procesando: '{query}'")
    print("Observa cómo los agentes deciden qué tools usar...\n")
    
    result = orchestrator.process_query(query)
    print_result(result)


def demo_2_query_vaga():
    """Demo 2: Query vaga que requiere optimización."""
    print_separator("🎬")
    print("DEMO 2: QUERY VAGA (El agente debe optimizarla)")
    print_separator("🎬")
    
    orchestrator = AutonomousOrchestrator()
    
    query = "dinosaurios"
    
    print(f"\n🔎 Procesando query vaga: '{query}'")
    print("Observa si RetrieverAgent decide usar optimize_search_query...\n")
    
    result = orchestrator.process_query(query)
    print_result(result)


def demo_3_comparacion():
    """Demo 3: Comparación de conceptos."""
    print_separator("🎬")
    print("DEMO 3: COMPARACIÓN DE CONCEPTOS")
    print_separator("🎬")
    
    orchestrator = AutonomousOrchestrator()
    
    query = "Compara los dinosaurios carnívoros con los herbívoros"
    
    print(f"\n🔎 Procesando: '{query}'")
    print("Observa cómo se clasifica como 'comparacion' y se adapta la búsqueda...\n")
    
    result = orchestrator.process_query(query)
    print_result(result)


def demo_4_resumen():
    """Demo 4: Solicitud de resumen."""
    print_separator("🎬")
    print("DEMO 4: RESUMEN DE DOCUMENTOS")
    print_separator("🎬")
    
    orchestrator = AutonomousOrchestrator()
    
    query = "Resume la información sobre fósiles de dinosaurios"
    
    print(f"\n🔎 Procesando: '{query}'")
    print("Observa cómo se recuperan más documentos (8-10) para resumen amplio...\n")
    
    result = orchestrator.process_query(query)
    print_result(result)


def demo_5_consulta_general():
    """Demo 5: Consulta general sin RAG."""
    print_separator("🎬")
    print("DEMO 5: CONSULTA GENERAL (Sin RAG)")
    print_separator("🎬")
    
    orchestrator = AutonomousOrchestrator()
    
    query = "Hola, ¿cómo estás?"
    
    print(f"\n🔎 Procesando: '{query}'")
    print("Observa cómo se clasifica como 'general' y NO se usa RAG...\n")
    
    result = orchestrator.process_query(query)
    print_result(result)


def demo_interactivo():
    """Demo interactivo: el usuario puede hacer consultas."""
    print_separator("🎬")
    print("DEMO INTERACTIVO")
    print("Haz tus propias consultas y observa cómo los agentes deciden")
    print_separator("🎬")
    
    orchestrator = AutonomousOrchestrator()
    
    print("\n💡 Ejemplos de consultas:")
    print("  • ¿Qué comían los T-Rex?")
    print("  • Compara dinosaurios voladores con terrestres")
    print("  • Resume información sobre extinción de dinosaurios")
    print("  • dinosaurios marinos")
    print("  • ¿Cómo funcionas?")
    print("\n  (escribe 'salir' para terminar)\n")
    
    while True:
        try:
            query = input("🔎 Tu consulta: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['salir', 'exit', 'quit']:
                print("\n👋 ¡Hasta luego!\n")
                break
            
            print(f"\n⚙️ Procesando: '{query}'")
            print("(Observa el log para ver las decisiones de los agentes)\n")
            
            result = orchestrator.process_query(query)
            print_result(result)
            
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!\n")
            break
        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=True)
            print(f"\n❌ Error: {str(e)}\n")


def main():
    """Función principal del demo."""
    print("\n" + "="*100)
    print(" " * 30 + "SISTEMA AGENTIC AI AUTÓNOMO")
    print(" " * 25 + "Demostración de Agentes con Tools")
    print("="*100)
    
    print("\n📋 Menú de Demos:")
    print("  1. Búsqueda Simple")
    print("  2. Query Vaga (optimización automática)")
    print("  3. Comparación de Conceptos")
    print("  4. Resumen de Documentos")
    print("  5. Consulta General (sin RAG)")
    print("  6. Modo Interactivo")
    print("  7. Ejecutar Todos los Demos")
    print("  0. Salir")
    
    try:
        opcion = input("\n🎯 Selecciona una opción (0-7): ").strip()
        
        if opcion == "1":
            demo_1_busqueda_simple()
        elif opcion == "2":
            demo_2_query_vaga()
        elif opcion == "3":
            demo_3_comparacion()
        elif opcion == "4":
            demo_4_resumen()
        elif opcion == "5":
            demo_5_consulta_general()
        elif opcion == "6":
            demo_interactivo()
        elif opcion == "7":
            demo_1_busqueda_simple()
            input("\n⏸️ Presiona Enter para continuar...")
            demo_2_query_vaga()
            input("\n⏸️ Presiona Enter para continuar...")
            demo_3_comparacion()
            input("\n⏸️ Presiona Enter para continuar...")
            demo_4_resumen()
            input("\n⏸️ Presiona Enter para continuar...")
            demo_5_consulta_general()
        elif opcion == "0":
            print("\n👋 ¡Hasta luego!\n")
        else:
            print("\n❌ Opción inválida\n")
    
    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego!\n")
    except Exception as e:
        logger.error(f"Error en demo: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {str(e)}\n")


if __name__ == "__main__":
    main()
