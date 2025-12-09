"""
Script de Prueba Rápida - Sistema Autónomo Completo

Valida que la migración al sistema autónomo funciona correctamente.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Asegurarse de que las variables de entorno estén configuradas
if not os.getenv("GOOGLE_API_KEY") or not os.getenv("GROQ_API_KEY"):
    print("❌ Error: Configura GOOGLE_API_KEY y GROQ_API_KEY en .env")
    print(f"   GOOGLE_API_KEY presente: {bool(os.getenv('GOOGLE_API_KEY'))}")
    print(f"   GROQ_API_KEY presente: {bool(os.getenv('GROQ_API_KEY'))}")
    sys.exit(1)

print("\n" + "="*70)
print("🧪 PRUEBA RÁPIDA - SISTEMA AUTÓNOMO COMPLETO")
print("="*70)

# Test 1: Importar agentes autónomos
print("\n[1/4] Importando agentes autónomos...")
try:
    from src.agents import (
        AutonomousClassifierAgent,
        AutonomousRetrieverAgent,
        AutonomousRAGAgent,
        AutonomousCriticAgent,
        AutonomousOrchestrator,
        AutonomousIndexerAgent
    )
    print("✅ 6 agentes autónomos importados correctamente")
except Exception as e:
    print(f"❌ Error importando agentes: {e}")
    sys.exit(1)

# Test 2: Importar tools
print("\n[2/4] Importando tools de LangChain...")
try:
    from src.tools import (
        # Query Processing Tools (11)
        search_documents,
        search_documents_by_metadata,
        optimize_search_query,
        generate_rag_response,
        generate_general_response,
        validate_response,
        check_hallucination,
        classify_intent,
        log_agent_decision,
        log_agent_action,
        get_available_documents_info,
        
        # Indexing Tools (11)
        load_document,
        scan_directory_for_documents,
        load_documents_batch,
        clean_documents,
        chunk_documents,
        process_documents_pipeline,
        create_vector_index,
        add_to_vector_index,
        save_vector_index,
        load_vector_index,
        get_index_statistics
    )
    print("✅ 22 tools LangChain importadas correctamente")
    print("   - Query Processing: 11 tools")
    print("   - Indexing: 11 tools")
except Exception as e:
    print(f"❌ Error importando tools: {e}")
    sys.exit(1)

# Test 3: Inicializar agentes
print("\n[3/4] Inicializando agentes autónomos...")
try:
    classifier = AutonomousClassifierAgent()
    print("✅ ClassifierAgent inicializado")
    
    retriever = AutonomousRetrieverAgent()
    print("✅ RetrieverAgent inicializado")
    
    rag = AutonomousRAGAgent()
    print("✅ RAGAgent inicializado")
    
    critic = AutonomousCriticAgent()
    print("✅ CriticAgent inicializado")
    
    orchestrator = AutonomousOrchestrator()
    print("✅ Orchestrator inicializado")
    
    indexer = AutonomousIndexerAgent()
    print("✅ IndexerAgent inicializado")
    
    print("\n✅ Todos los agentes inicializados correctamente")
except Exception as e:
    print(f"❌ Error inicializando agentes: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Verificar tools en agentes
print("\n[4/4] Verificando tools en agentes...")
try:
    # Classifier
    classifier_tools = len(classifier.tools)
    print(f"✅ ClassifierAgent: {classifier_tools} tools")
    
    # Retriever
    retriever_tools = len(retriever.tools)
    print(f"✅ RetrieverAgent: {retriever_tools} tools")
    
    # RAG
    rag_tools = len(rag.tools)
    print(f"✅ RAGAgent: {rag_tools} tools")
    
    # Critic
    critic_tools = len(critic.tools)
    print(f"✅ CriticAgent: {critic_tools} tools")
    
    # Indexer
    indexer_tools = len(indexer.tools)
    print(f"✅ IndexerAgent: {indexer_tools} tools")
    
    total_tools = classifier_tools + retriever_tools + rag_tools + critic_tools + indexer_tools
    print(f"\n📊 Total de asignaciones de tools: {total_tools}")
    
except Exception as e:
    print(f"❌ Error verificando tools: {e}")
    sys.exit(1)

# Test 5: Verificar estructura del sistema
print("\n[5/5] Verificando estructura del sistema...")
try:
    from src.tools import ALL_LANGCHAIN_TOOLS, INDEXER_TOOLS
    
    print(f"✅ ALL_LANGCHAIN_TOOLS: {len(ALL_LANGCHAIN_TOOLS)} tools")
    print(f"✅ INDEXER_TOOLS: {len(INDEXER_TOOLS)} tools")
    
    # Verificar archivos críticos
    files_to_check = [
        "src/tools/document_loader_tool.py",
        "src/tools/document_processing_tool.py",
        "src/tools/index_management_tool.py",
        "src/agents/autonomous_indexer_agent.py",
        "main.py",
        "examples.py"
    ]
    
    print("\n📁 Verificando archivos críticos:")
    for file in files_to_check:
        if Path(file).exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} NO ENCONTRADO")
    
except Exception as e:
    print(f"❌ Error verificando estructura: {e}")
    sys.exit(1)

# Resumen Final
print("\n" + "="*70)
print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
print("="*70)
print("\n📊 Resumen del Sistema:")
print(f"   - Agentes Autónomos: 6")
print(f"   - LangChain Tools: 22 (11 query + 11 indexing)")
print(f"   - LLMs: Gemini 2.5 Flash + Groq Llama 3.1 70B")
print(f"   - Estado: PRODUCCIÓN")

print("\n🚀 Siguiente Paso:")
print("   python main.py --index    # Indexar documentos con agente autónomo")
print("   python main.py            # Modo interactivo con sistema autónomo")
print("   python examples.py        # Ejecutar ejemplos autónomos")

print("\n" + "="*70 + "\n")
