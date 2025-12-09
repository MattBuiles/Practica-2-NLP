"""
Sistema Agentic AI Multi-Agente con LangChain 1.0
Práctica 3 - Procesamiento de Lenguaje Natural

Sistema de RAG con agentes especializados para procesamiento
de documentos, clasificación de intención, recuperación semántica
y generación de respuestas validadas.
"""
import os
import sys
import logging
from pathlib import Path

# Configurar logging
from src.tools.logger_tool import LoggerTool
LoggerTool.setup_logging(log_level="INFO", log_to_file=True)

logger = logging.getLogger(__name__)

from src.config.paths import create_directories, RAW_DATA_DIR
from src.agents.autonomous_orchestrator import AutonomousOrchestrator
from src.agents.autonomous_indexer_agent import AutonomousIndexerAgent
from src.rag_pipeline.pipelines import RAGPipeline
from src.tools.trace_exporter import TraceExporterTool


def initialize_system():
    """Inicializa el sistema y crea directorios necesarios."""
    logger.info("=== Inicializando Sistema Agentic AI ===")
    
    # Crear estructura de directorios
    create_directories()
    logger.info("Directorios del sistema creados")
    
    # Verificar variables de entorno
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY no encontrada en variables de entorno")
        print("❌ Error: Configura GOOGLE_API_KEY en el archivo .env")
        sys.exit(1)
    
    if not os.getenv("GROQ_API_KEY"):
        logger.error("GROQ_API_KEY no encontrada en variables de entorno")
        print("❌ Error: Configura GROQ_API_KEY en el archivo .env")
        sys.exit(1)
    
    logger.info("Variables de entorno verificadas ✓")


def index_documents(documents_path: str = None):
    """
    Indexa documentos desde un directorio usando el Agente Indexador Autónomo.
    
    Args:
        documents_path: Ruta del directorio con documentos (usa RAW_DATA_DIR por defecto)
    """
    if documents_path is None:
        documents_path = str(RAW_DATA_DIR)
    
    logger.info(f"=== Indexación Autónoma desde: {documents_path} ===")
    
    # Verificar que existe el directorio
    doc_path = Path(documents_path)
    if not doc_path.exists():
        logger.error(f"Directorio no existe: {documents_path}")
        print(f"❌ Error: El directorio {documents_path} no existe")
        print(f"📁 Coloca tus documentos en: {RAW_DATA_DIR}")
        return False
    
    print(f"\n🤖 Iniciando Agente Indexador Autónomo...")
    print(f"📁 Directorio: {documents_path}\n")
    
    # Usar agente autónomo para indexación
    indexer = AutonomousIndexerAgent()
    result = indexer.index_directory(
        directory_path=documents_path,
        file_types="pdf,html,txt",
        clean_aggressive=False,
        save_index=True
    )
    
    if result['status'] == 'success':
        print("\n" + "="*60)
        print("✅ INDEXACIÓN COMPLETADA EXITOSAMENTE")
        print("="*60)
        print(result['response'])
        print("="*60)
        
        # Mostrar trace de decisiones
        if result.get('intermediate_steps'):
            print("\n🔍 Trazabilidad de Decisiones:")
            for i, step in enumerate(result['intermediate_steps'][:5], 1):
                action = step[0] if isinstance(step, tuple) else step
                print(f"   {i}. {action.tool if hasattr(action, 'tool') else 'Acción'}")
        
        logger.info("Indexación autónoma completada exitosamente")
        return True
    else:
        print(f"\n❌ Error en indexación: {result.get('error', 'Unknown error')}")
        logger.error(f"Error en indexación autónoma: {result.get('error')}")
        return False


def interactive_mode():
    """Modo interactivo para consultas usando el Sistema Autónomo."""
    logger.info("=== Iniciando modo interactivo autónomo ===")
    
    # Cargar índice existente usando agente indexador
    indexer = AutonomousIndexerAgent()
    try:
        print("\n🤖 Cargando índice vectorial...")
        result = indexer.load_existing_index()
        
        if result['status'] != 'success':
            print("❌ Error: No se pudo cargar el índice de documentos")
            print("💡 Ejecuta primero: python main.py --index")
            return
        
        stats_result = indexer.get_stats()
        
        print("\n" + "="*60)
        print("🤖 Sistema Agentic AI Autónomo - Modo Interactivo")
        print("="*60)
        print("✅ Índice cargado exitosamente")
        print(f"🔧 Agentes autónomos: Classifier, Retriever, RAG, Critic")
        print(f"📊 Sistema listo para consultas")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Error al cargar índice: {str(e)}")
        print("❌ Error: No se pudo cargar el índice de documentos")
        print("💡 Ejecuta primero: python main.py --index")
        return
    
    # Inicializar orquestador autónomo
    orchestrator = AutonomousOrchestrator()
    
    print("Escribe tu consulta (o 'salir' para terminar)\n")
    
    case_number = 1
    
    while True:
        try:
            # Obtener consulta
            query = input("🔍 Consulta: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['salir', 'exit', 'quit']:
                print("\n👋 ¡Hasta luego!")
                break
            
            # Procesar consulta
            print("\n⏳ Procesando...\n")
            result = orchestrator.process_query(query, include_trace=True)
            
            # Mostrar respuesta
            print("="*60)
            print("📝 RESPUESTA:")
            print("="*60)
            print(result['response'])
            print("\n" + "="*60)
            
            # Mostrar metadata
            print(f"\n📊 Metadata:")
            print(f"   - Intención: {result.get('intent', 'N/A')}")
            print(f"   - Documentos consultados: {result.get('documents_found', 0)}")
            print(f"   - Regeneraciones: {result.get('regeneration_attempts', 0)}")
            
            if result.get('validation'):
                val = result['validation']
                print(f"   - Score de validación: {val.get('overall_score', 0):.2f}")
            
            print("="*60 + "\n")
            
            # Preguntar si exportar como caso de uso
            export = input("💾 ¿Exportar como caso de uso? (s/n): ").strip().lower()
            if export == 's':
                TraceExporterTool.export_case_study(
                    case_number=case_number,
                    query=query,
                    response=result['response'],
                    trace_data=result.get('trace', {}),
                    domain="salud"  # Cambiar según tu dominio
                )
                print(f"✅ Caso de uso #{case_number} exportado\n")
                case_number += 1
            
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            logger.error(f"Error en modo interactivo: {str(e)}", exc_info=True)
            print(f"\n❌ Error: {str(e)}\n")


def batch_mode(queries_file: str):
    """
    Procesa consultas desde un archivo usando el Sistema Autónomo.
    
    Args:
        queries_file: Archivo con consultas (una por línea)
    """
    logger.info(f"=== Modo batch autónomo: {queries_file} ===")
    
    # Leer consultas
    try:
        with open(queries_file, 'r', encoding='utf-8') as f:
            queries = [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Error leyendo archivo: {str(e)}")
        print(f"❌ Error leyendo {queries_file}: {str(e)}")
        return
    
    print(f"\n📋 Procesando {len(queries)} consultas con agentes autónomos...\n")
    
    # Cargar índice
    indexer = AutonomousIndexerAgent()
    indexer.load_existing_index()
    
    # Procesar consultas con orquestador autónomo
    orchestrator = AutonomousOrchestrator()
    results = []
    
    for i, query in enumerate(queries, 1):
        print(f"[{i}/{len(queries)}] Procesando: {query[:50]}...")
        result = orchestrator.process_query(query)
        results.append(result)
    
    # Exportar resultados
    TraceExporterTool.export_batch_results(results, batch_name="batch_queries_autonomous")
    
    print(f"\n✅ Procesamiento completado: {len(results)} resultados")
    print(f"📁 Resultados exportados a: results/respuestas/\n")


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Sistema Agentic AI Multi-Agente con RAG"
    )
    parser.add_argument(
        '--index',
        action='store_true',
        help='Indexar documentos desde data/raw/'
    )
    parser.add_argument(
        '--index-path',
        type=str,
        help='Ruta personalizada para indexar documentos'
    )
    parser.add_argument(
        '--batch',
        type=str,
        help='Procesar consultas desde archivo'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Modo interactivo (por defecto)'
    )
    
    args = parser.parse_args()
    
    # Inicializar sistema
    initialize_system()
    
    # Modo indexación
    if args.index or args.index_path:
        index_documents(args.index_path)
        return
    
    # Modo batch
    if args.batch:
        batch_mode(args.batch)
        return
    
    # Modo interactivo (por defecto)
    interactive_mode()


if __name__ == "__main__":
    main()
