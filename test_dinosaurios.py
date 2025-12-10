"""
Test de 10 Casos de Uso sobre Dinosaurios
Prueba el sistema RAG con consultas variadas sobre el dataset de dinosaurios.
Verifica el registro de trazas en logs/ y resultados en results/
"""
import os
import sys
from pathlib import Path
import json
from datetime import datetime
import subprocess
import time

# Configurar logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_dinosaurios.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Asegurarnos de que los directorios existen
Path("logs").mkdir(exist_ok=True)
Path("results").mkdir(exist_ok=True)

from src.agents.autonomous_orchestrator import AutonomousOrchestrator
from src.tools.trace_exporter import TraceExporterTool


# 10 Casos de Uso sobre Dinosaurios
CASOS_DE_USO = [
    {
        "numero": 1,
        "categoria": "Información General",
        "query": "¿Cuáles fueron los dinosaurios más grandes que existieron?",
        "descripcion": "Consulta sobre tamaño de dinosaurios - debe usar RAG simple"
    },
    {
        "numero": 2,
        "categoria": "General (sin RAG)",
        "query": "¡Hola! ¿Cómo estás hoy?",
        "descripcion": "Saludo general - debe ser clasificado como 'general' y no requerir RAG"
    },
    {
        "numero": 3,
        "categoria": "Evolución",
        "query": "¿Cómo evolucionaron las aves a partir de los dinosaurios?",
        "descripcion": "Consulta sobre evolución - puede requerir comparación de documentos"
    },
    {
        "numero": 4,
        "categoria": "Comportamiento",
        "query": "¿Fueron los dinosaurios buenos padres?",
        "descripcion": "Consulta sobre comportamiento - documento específico disponible"
    },
    {
        "numero": 5,
        "categoria": "Extinción",
        "query": "¿Cómo terminó un asteroide con la era de los dinosaurios?",
        "descripcion": "Consulta sobre extinción masiva - información histórica"
    },
    {
        "numero": 6,
        "categoria": "Especies Específicas",
        "query": "Cuéntame sobre el Spinosaurus y sus habilidades de caza",
        "descripcion": "Consulta sobre especie específica con comportamiento de caza"
    },
    {
        "numero": 7,
        "categoria": "Fósiles y Descubrimientos",
        "query": "¿Qué nos revelan las huellas de dinosaurio?",
        "descripcion": "Consulta sobre evidencia fósil - paleontología"
    },
    {
        "numero": 8,
        "categoria": "Anatomía Comparativa",
        "query": "¿Cuáles son las diferencias entre dinosaurios carnívoros y herbívoros?",
        "descripcion": "Comparación entre tipos de dinosaurios - requiere comparison_rag"
    },
    {
        "numero": 9,
        "categoria": "Paleontología Moderna",
        "query": "¿Cómo se preparan los fósiles para exhibición en museos?",
        "descripcion": "Consulta sobre métodos científicos actuales"
    },
    {
        "numero": 10,
        "categoria": "Resumen",
        "query": "Resume la información disponible sobre los trilobites",
        "descripcion": "Resumen de documentos - requiere summary_rag sobre trilobites"
    }
]


def verificar_entorno():
    """Verifica que el sistema esté configurado correctamente."""
    print("\n" + "="*70)
    print("🔍 VERIFICACIÓN DEL ENTORNO")
    print("="*70)
    
    # Verificar API keys
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY no configurada")
        return False
    
    if not os.getenv("GROQ_API_KEY"):
        print("❌ Error: GROQ_API_KEY no configurada")
        return False
    
    print("✅ API Keys configuradas")
    
    # Verificar vectorstore
    vectorstore_path = Path("data/vectorstore")
    if not vectorstore_path.exists() or not list(vectorstore_path.glob("*")):
        print("⚠️  Advertencia: No se encontró vectorstore")
        print("   Ejecuta primero: python main.py --index")
        return False
    
    print("✅ Vectorstore encontrado")
    
    # Crear directorios de logs y resultados
    logs_dir = Path("logs")
    results_dir = Path("results/casos_de_uso")
    respuestas_dir = Path("results/respuestas")
    
    logs_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    respuestas_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"✅ Directorio de logs: {logs_dir}")
    print(f"✅ Directorio de resultados: {results_dir}")
    print(f"✅ Directorio de respuestas: {respuestas_dir}")
    
    print("="*70 + "\n")
    return True


def verificar_archivos_generados():
    """Verifica que se hayan generado logs y resultados."""
    print("\n" + "="*70)
    print("🔍 VERIFICACIÓN DE ARCHIVOS GENERADOS")
    print("="*70)
    
    verificaciones = []
    
    # Verificar logs
    logs_dir = Path("logs")
    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.log"))
        if log_files:
            print(f"\n✅ Logs generados ({len(log_files)} archivos):")
            for log_file in sorted(log_files):
                size_kb = log_file.stat().st_size / 1024
                print(f"   - {log_file.name} ({size_kb:.2f} KB)")
            verificaciones.append(True)
        else:
            print("\n❌ No se encontraron archivos de log")
            verificaciones.append(False)
    else:
        print("\n❌ Directorio logs/ no existe")
        verificaciones.append(False)
    
    # Verificar resultados de casos de uso
    casos_dir = Path("results/casos_de_uso")
    if casos_dir.exists():
        caso_files = list(casos_dir.glob("*.json"))
        if caso_files:
            print(f"\n✅ Casos de uso guardados ({len(caso_files)} archivos):")
            for caso_file in sorted(caso_files)[:10]:  # Mostrar máximo 10
                print(f"   - {caso_file.name}")
            if len(caso_files) > 10:
                print(f"   ... y {len(caso_files) - 10} más")
            verificaciones.append(True)
        else:
            print("\n❌ No se encontraron casos de uso guardados")
            verificaciones.append(False)
    else:
        print("\n❌ Directorio results/casos_de_uso/ no existe")
        verificaciones.append(False)
    
    # Verificar batch results
    respuestas_dir = Path("results/respuestas")
    if respuestas_dir.exists():
        batch_files = list(respuestas_dir.glob("*.json"))
        if batch_files:
            print(f"\n✅ Resultados batch guardados ({len(batch_files)} archivos):")
            for batch_file in sorted(batch_files):
                size_kb = batch_file.stat().st_size / 1024
                print(f"   - {batch_file.name} ({size_kb:.2f} KB)")
            verificaciones.append(True)
        else:
            print("\n⚠️  No se encontraron archivos batch (puede ser normal)")
            verificaciones.append(True)  # No es error crítico
    else:
        print("\n⚠️  Directorio results/respuestas/ no existe")
        verificaciones.append(True)  # No es error crítico
    
    # Verificar resumen del test
    summary_file = Path("results/test_dinosaurios_summary.json")
    if summary_file.exists():
        size_kb = summary_file.stat().st_size / 1024
        print(f"\n✅ Resumen del test: {summary_file.name} ({size_kb:.2f} KB)")
        verificaciones.append(True)
    else:
        print(f"\n❌ No se encontró el resumen: {summary_file}")
        verificaciones.append(False)
    
    print("\n" + "="*70)
    
    # Retornar si todas las verificaciones críticas pasaron
    return all(verificaciones[:3])  # Solo las primeras 3 son críticas


def ejecutar_caso_de_uso(caso: dict, orchestrator: AutonomousOrchestrator):
    """
    Ejecuta un caso de uso individual.
    
    Args:
        caso: Diccionario con información del caso
        orchestrator: Instancia del orquestador autónomo
    
    Returns:
        Resultado del procesamiento
    """
    print("\n" + "="*70)
    print(f"📋 CASO #{caso['numero']}: {caso['categoria']}")
    print("="*70)
    print(f"❓ Query: {caso['query']}")
    print(f"📝 Descripción: {caso['descripcion']}")
    print("-"*70)
    
    try:
        # Procesar query con el orchestrator
        start_time = datetime.now()
        result = orchestrator.process_query(caso['query'])
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Registrar en logs
        logger.info(f"Caso #{caso['numero']} completado - {caso['categoria']}")
        logger.info(f"Query: {caso['query']}")
        logger.info(f"Estrategia: {result.get('strategy', 'N/A')}")
        logger.info(f"Tiempo: {execution_time:.2f}s")
        
        # Mostrar resultados
        print(f"\n💬 Respuesta:\n{result.get('response', 'Sin respuesta')}\n")
        print("-"*70)
        print(f"📊 Metadata:")
        print(f"   - Estrategia: {result.get('strategy', 'N/A')}")
        print(f"   - Intención: {result.get('intent', 'N/A')}")
        print(f"   - Documentos: {result.get('documents_used', 0)}")
        print(f"   - Tiempo: {execution_time:.2f}s")
        print(f"   - Validación: {'✅ Aprobada' if result.get('validation_passed') else '⚠️ Con observaciones'}")
        
        # Preparar datos para exportación
        trace_data = {
            "intent": result.get('intent'),
            "strategy": result.get('strategy'),
            "documents_used": result.get('documents_used', 0),
            "execution_time": execution_time,
            "validation_passed": result.get('validation_passed', False),
            "intermediate_steps": len(result.get('intermediate_steps', [])),
            "agents_called": ["classifier", "retriever", "rag_agent", "critic"],
            "tools_used": result.get('tools_used', [])
        }
        
        # Exportar caso de estudio (esto guarda en results/)
        export_path = TraceExporterTool.export_case_study(
            case_number=caso['numero'],
            query=caso['query'],
            response=result.get('response', ''),
            trace_data=trace_data,
            domain="dinosaurios"
        )
        
        if export_path:
            print(f"   - Exportado: ✅ {Path(export_path).name}")
            logger.info(f"Caso exportado en: {export_path}")
        
        print("="*70)
        
        # Retornar resumen del resultado
        return {
            "caso": caso['numero'],
            "categoria": caso['categoria'],
            "query": caso['query'],
            "response": result.get('response', ''),
            "intent": result.get('intent'),
            "strategy": result.get('strategy'),
            "documents_used": result.get('documents_used', 0),
            "execution_time": execution_time,
            "validation_passed": result.get('validation_passed', False),
            "export_path": export_path
        }
        
    except Exception as e:
        logger.error(f"Error en caso #{caso['numero']}: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
        print("="*70)
        return {
            "caso": caso['numero'],
            "categoria": caso['categoria'],
            "query": caso['query'],
            "error": str(e)
        }


def generar_reporte_final(resultados: list):
    """
    Genera un reporte final con estadísticas de todos los casos.
    
    Args:
        resultados: Lista de resultados de cada caso
    """
    print("\n" + "="*70)
    print("📊 REPORTE FINAL - TEST DE DINOSAURIOS")
    print("="*70)
    
    exitosos = [r for r in resultados if 'error' not in r]
    errores = [r for r in resultados if 'error' in r]
    
    print(f"\n✅ Casos exitosos: {len(exitosos)}/{len(resultados)}")
    print(f"❌ Casos con error: {len(errores)}/{len(resultados)}")
    
    # Registrar en logs
    logger.info(f"=== REPORTE FINAL ===")
    logger.info(f"Casos exitosos: {len(exitosos)}/{len(resultados)}")
    logger.info(f"Casos con error: {len(errores)}/{len(resultados)}")
    
    if exitosos:
        print("\n📈 Estadísticas:")
        
        # Tiempo promedio
        tiempo_promedio = sum(r['execution_time'] for r in exitosos) / len(exitosos)
        print(f"   - Tiempo promedio: {tiempo_promedio:.2f}s")
        logger.info(f"Tiempo promedio: {tiempo_promedio:.2f}s")
        
        # Documentos promedio
        docs_promedio = sum(r['documents_used'] for r in exitosos) / len(exitosos)
        print(f"   - Documentos promedio: {docs_promedio:.1f}")
        logger.info(f"Documentos promedio: {docs_promedio:.1f}")
        
        # Distribución de intenciones
        intenciones = {}
        for r in exitosos:
            intent = r.get('intent', 'unknown')
            intenciones[intent] = intenciones.get(intent, 0) + 1
        
        print(f"\n🎯 Distribución de Intenciones:")
        for intent, count in intenciones.items():
            print(f"   - {intent}: {count}")
            logger.info(f"Intención {intent}: {count} casos")
        
        # Distribución de estrategias
        estrategias = {}
        for r in exitosos:
            strategy = r.get('strategy', 'unknown')
            estrategias[strategy] = estrategias.get(strategy, 0) + 1
        
        print(f"\n🔧 Distribución de Estrategias:")
        for strategy, count in estrategias.items():
            print(f"   - {strategy}: {count}")
            logger.info(f"Estrategia {strategy}: {count} casos")
        
        # Validación
        validados = sum(1 for r in exitosos if r.get('validation_passed'))
        print(f"\n✓ Casos validados exitosamente: {validados}/{len(exitosos)}")
        logger.info(f"Casos validados: {validados}/{len(exitosos)}")
    
    # Exportar batch results (guarda en results/respuestas/)
    print("\n📦 Exportando resultados batch...")
    batch_path = TraceExporterTool.export_batch_results(
        results=resultados,
        batch_name="test_dinosaurios"
    )
    
    if batch_path:
        print(f"✅ Batch exportado: {Path(batch_path).name}")
        logger.info(f"Batch exportado en: {batch_path}")
    
    print("\n" + "="*70)
    print("🎉 TEST COMPLETADO")
    print("="*70)
    print(f"\n📁 Revisa los resultados en: results/casos_de_uso/")
    print(f"📁 Revisa el batch en: results/respuestas/")
    print(f"📁 Revisa los logs en: logs/")
    print()
    
    logger.info("Test completado exitosamente")


def main():
    """Función principal del test."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test de Sistema RAG - Dinosaurios')
    parser.add_argument('--casos', '-n', type=int, default=10, 
                       help='Número de casos a ejecutar (default: 10)')
    parser.add_argument('--debug', '-d', action='store_true',
                       help='Modo debug: ejecuta solo 2 casos')
    args = parser.parse_args()
    
    num_casos = 2 if args.debug else args.casos
    casos_a_ejecutar = CASOS_DE_USO[:num_casos]
    
    print("\n" + "="*70)
    print("🦖 TEST DE SISTEMA RAG - DINOSAURIOS")
    print("="*70)
    print(f"Ejecutando {len(casos_a_ejecutar)} casos de uso sobre el dataset de dinosaurios")
    print("="*70 + "\n")
    
    logger.info("=== Iniciando Test de Dinosaurios ===")
    
    # Verificar entorno
    if not verificar_entorno():
        print("\n❌ Verifica la configuración antes de continuar")
        logger.error("Verificación de entorno fallida")
        sys.exit(1)
    
    logger.info("Verificación de entorno exitosa")
    
    # Inicializar orchestrator
    print("🤖 Inicializando Orchestrator Autónomo...\n")
    try:
        orchestrator = AutonomousOrchestrator()
        print("✅ Orchestrator inicializado\n")
        logger.info("Orchestrator inicializado correctamente")
    except Exception as e:
        print(f"❌ Error inicializando orchestrator: {str(e)}")
        logger.error(f"Error inicializando orchestrator: {str(e)}", exc_info=True)
        sys.exit(1)
    
    # Ejecutar casos de uso
    resultados = []
    
    print("🚀 Iniciando casos de uso...\n")
    logger.info(f"Ejecutando {len(casos_a_ejecutar)} casos de uso")
    
    for caso in casos_a_ejecutar:
        resultado = ejecutar_caso_de_uso(caso, orchestrator)
        resultados.append(resultado)
        
        # Pausa breve entre casos para evitar rate limiting
        print("\n⏳ Pausa entre casos (3s)...")
        time.sleep(3)
    
    # Generar reporte final
    generar_reporte_final(resultados)
    
    # Guardar resultados en JSON
    output_file = Path("results/test_dinosaurios_summary.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_casos": len(CASOS_DE_USO),
            "resultados": resultados
        }, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Resumen guardado en: {output_file}")
    logger.info(f"Resumen guardado en: {output_file}")
    
    # Verificar que se generaron los archivos
    print("\n" + "="*70)
    print("🔍 VERIFICANDO ARCHIVOS GENERADOS")
    print("="*70)
    
    if verificar_archivos_generados():
        print("\n✅ VERIFICACIÓN EXITOSA: Todos los archivos fueron generados")
        logger.info("Verificación de archivos exitosa")
        print()
        return 0
    else:
        print("\n⚠️  ADVERTENCIA: Algunos archivos no fueron generados correctamente")
        logger.warning("Verificación de archivos incompleta")
        print()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
