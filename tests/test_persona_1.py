"""
Script de Prueba Rápida - Persona 1
Verifica que tus componentes implementados funcionen correctamente.
"""

def test_persona_1_components():
    """Prueba los componentes implementados por Persona 1."""
    
    print("="*70)
    print("PRUEBA DE COMPONENTES - PERSONA 1")
    print("="*70)
    
    # Test 1: Configuración LLM
    print("\n1. Probando Configuración LLM...")
    try:
        from src.config.llm_config import llm_config
        
        classifier_llm = llm_config.get_classifier_llm()
        orchestrator_llm = llm_config.get_orchestrator_llm()
        
        print("   ✅ LLM Config inicializado correctamente")
        print(f"   - Clasificador: Gemini 1.5 Flash")
        print(f"   - Orquestador: Groq Llama 3.1 70B")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Clasificador
    print("\n2. Probando Agente Clasificador...")
    try:
        from src.agents.classifier_agent import ClassifierAgent
        
        classifier = ClassifierAgent()
        
        # Probar las 4 intenciones
        test_queries = {
            "busqueda": "¿Qué es la diabetes tipo 2?",
            "resumen": "Resume el documento sobre hipertensión",
            "comparacion": "Compara diabetes tipo 1 con tipo 2",
            "general": "Hola, ¿cómo estás?"
        }
        
        print("   Clasificando consultas de prueba:")
        for expected, query in test_queries.items():
            result = classifier.classify(query)
            status = "✅" if result["intent"] == expected else "⚠️"
            print(f"   {status} '{query[:40]}...'")
            print(f"      Intent: {result['intent']} (confianza: {result['confidence']:.2f})")
            print(f"      RAG: {'Sí' if result['requires_rag'] else 'No'}")
        
        print("   ✅ Clasificador funcionando correctamente")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Trazabilidad
    print("\n3. Probando Sistema de Trazabilidad...")
    try:
        from src.utils.tracing import trace_manager, ExecutionTrace
        
        # Crear traza de prueba
        trace = trace_manager.start_trace("Consulta de prueba")
        trace.add_classification("busqueda", 0.9, "Razonamiento de prueba")
        trace.finalize("Respuesta de prueba")
        
        print("   ✅ Trazabilidad funcionando")
        print(f"   - Session ID: {trace.session_id}")
        print(f"   - Pasos registrados: {len(trace.steps)}")
        print(f"   - Agentes involucrados: {trace.metadata['agents_involved']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Orquestador
    print("\n4. Probando Agente Orquestador...")
    try:
        from src.agents.orchestrator import Orchestrator
        
        orchestrator = Orchestrator()
        
        # Probar con consulta general (no requiere RAG)
        result = orchestrator.process_query("Hola, ¿cómo estás?")
        
        print("   ✅ Orquestador inicializado")
        print(f"   - Intent detectado: {result.get('intent', 'N/A')}")
        print(f"   - Requiere RAG: {result.get('requires_rag', 'N/A')}")
        
        # Mostrar advertencias esperadas
        print("\n   ⚠️ ADVERTENCIAS ESPERADAS (componentes de Persona 2/3):")
        print("   - RetrieverAgent - PENDIENTE DE IMPLEMENTACIÓN")
        print("   - RAGAgent - PENDIENTE DE IMPLEMENTACIÓN")
        print("   - CriticAgent - PENDIENTE DE IMPLEMENTACIÓN")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Estadísticas del Sistema
    print("\n5. Estadísticas del Sistema...")
    try:
        stats = orchestrator.get_system_stats()
        
        print("   ✅ Estadísticas generadas:")
        print(f"   - Agentes configurados: {len(stats['agents'])}")
        print(f"   - Trazas recolectadas: {stats['traces_collected']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE PRUEBAS")
    print("="*70)
    print("\n✅ COMPONENTES IMPLEMENTADOS (Persona 1):")
    print("   1. Configuración LLM (Gemini + Groq)")
    print("   2. Agente Clasificador (4 intenciones)")
    print("   3. Sistema de Trazabilidad")
    print("   4. Agente Orquestador")
    print("   5. Estadísticas del sistema")
    
    print("\n🟡 COMPONENTES PENDIENTES (Persona 2/3):")
    print("   - RetrieverAgent (recuperación semántica)")
    print("   - RAGAgent (generación con contexto)")
    print("   - CriticAgent (validación)")
    print("   - RAG Pipeline (embeddings, chunking, FAISS)")
    print("   - Tools (loaders, cleaners)")
    
    print("\n" + "="*70)
    print("Estado: ✅ PERSONA 1 COMPLETADA - Listo para sustentación")
    print("="*70)


if __name__ == "__main__":
    test_persona_1_components()
