# 🔄 Guía de Migración: De Agentes Clásicos a Autónomos

## 📋 Resumen de Cambios

Has implementado con éxito **agentes autónomos** que usan **LangChain Tools** para tomar decisiones independientes. Esta guía te ayudará a integrarlos con tu código existente.

---

## 🆕 Archivos Nuevos Creados

### Tools (src/tools/)
```
✅ document_search_tool.py          # Búsqueda semántica
✅ query_optimizer_tool.py          # Optimización de queries
✅ response_generator_tool.py       # Generación RAG y general
✅ validation_tool.py               # Validación y alucinaciones
✅ intent_classifier_tool.py        # Clasificación de intención
✅ logging_tool.py                  # Trazabilidad
```

### Agentes Autónomos (src/agents/)
```
✅ autonomous_classifier_agent.py
✅ autonomous_retriever_agent.py
✅ autonomous_rag_agent.py
✅ autonomous_critic_agent.py
✅ autonomous_orchestrator.py
```

### Documentación (docs/)
```
✅ AUTONOMOUS_AGENTS_GUIDE.md       # Guía completa de tools y agentes
✅ INFORME_TEMPLATE_TOOLS_AGENTS.md # Plantilla para informe técnico
✅ VIDEO_PITCH_GUIDE.md             # Guía para video demostración
```

### Scripts de Demo
```
✅ demo_autonomous_system.py        # Demo interactivo
✅ AUTONOMOUS_SYSTEM_SUMMARY.md     # Resumen ejecutivo
```

---

## 🔧 Cómo Integrar con Tu Código Existente

### Opción 1: Reemplazar Orchestrator (Recomendado)

Si quieres usar el sistema autónomo completo:

```python
# ANTES (main.py, examples.py, etc.)
from src.agents import Orchestrator

orchestrator = Orchestrator()
result = orchestrator.process_query("¿Qué es un dinosaurio?")

# DESPUÉS (con agentes autónomos)
from src.agents import AutonomousOrchestrator

orchestrator = AutonomousOrchestrator()
result = orchestrator.process_query("¿Qué es un dinosaurio?")

# ¡El API es compatible! Mismo formato de entrada/salida
```

**Beneficios:**
- Autonomía real de agentes
- Uso inteligente de tools
- Trazabilidad completa
- Adaptación contextual

---

### Opción 2: Usar Agentes Individuales

Si solo quieres probar agentes autónomos específicos:

```python
# Clasificador autónomo
from src.agents import AutonomousClassifierAgent

classifier = AutonomousClassifierAgent()
classification = classifier.classify("Compara dinosaurios carnívoros y herbívoros")

print(f"Intención: {classification['intent']}")
print(f"Razonamiento: {classification['reasoning']}")
print(f"Tools usadas: {len(classification['intermediate_steps'])}")
```

```python
# Recuperador autónomo
from src.agents import AutonomousRetrieverAgent

retriever = AutonomousRetrieverAgent()
retrieval = retriever.retrieve(
    query="dinosaurios voladores",
    intent="busqueda"
)

print(f"Documentos: {len(retrieval['documents'])}")
print(f"Query usada: {retrieval['query_used']}")
print(f"Pasos: {retrieval['intermediate_steps']}")
```

---

### Opción 3: Sistema Híbrido

Puedes usar agentes clásicos para algunas tareas y autónomos para otras:

```python
from src.agents import (
    ClassifierAgent,              # Clásico
    AutonomousRetrieverAgent,     # Autónomo
    AutonomousRAGAgent,           # Autónomo
    CriticAgent                   # Clásico
)

# Clasificar con agente clásico (más rápido, menos flexible)
classifier = ClassifierAgent()
classification = classifier.classify(query)

# Recuperar con agente autónomo (más inteligente)
retriever = AutonomousRetrieverAgent()
retrieval = retriever.retrieve(query, classification['intent'])

# Generar con agente autónomo (adapta estilo)
rag_agent = AutonomousRAGAgent()
generation = rag_agent.generate(
    query, 
    retrieval['documents'], 
    classification['intent']
)

# Validar con agente clásico (más rápido)
critic = CriticAgent()
validation = critic.validate(query, generation['response'], retrieval['documents'])
```

---

## 📝 Actualizar Scripts Existentes

### Actualizar main.py

```python
# ANTES
def main():
    from src.agents import Orchestrator
    
    orchestrator = Orchestrator()
    query = input("Tu consulta: ")
    result = orchestrator.process_query(query)
    print(result['response'])

# DESPUÉS (con autonomía)
def main():
    from src.agents import AutonomousOrchestrator
    
    orchestrator = AutonomousOrchestrator()
    query = input("Tu consulta: ")
    result = orchestrator.process_query(query)
    
    # Mostrar respuesta
    print(result['response'])
    
    # Mostrar trazabilidad (NUEVO)
    print(f"\n📊 Agentes: {result['trace']['agents_called']}")
    print(f"🔧 Tools: {result['trace']['tools_used']}")
    print(f"⏱️ Tiempo: {result['execution_time']:.2f}s")
```

### Actualizar examples.py

```python
# ANTES
from src.agents import Orchestrator

def example_busqueda():
    orchestrator = Orchestrator()
    result = orchestrator.process_query("¿Qué es un T-Rex?")
    print(result['response'])

# DESPUÉS (con más información)
from src.agents import AutonomousOrchestrator

def example_busqueda():
    orchestrator = AutonomousOrchestrator()
    result = orchestrator.process_query("¿Qué es un T-Rex?")
    
    print("=" * 80)
    print("RESPUESTA:")
    print("=" * 80)
    print(result['response'])
    
    print("\n" + "=" * 80)
    print("TRAZABILIDAD:")
    print("=" * 80)
    print(f"Intent: {result['intent']}")
    print(f"Documentos: {result['documents_used']}")
    print(f"Validación: {result['validation']['confidence_score']:.2f}")
    print(f"Agentes: {', '.join(result['trace']['agents_called'])}")
    print(f"Tools: {', '.join(result['trace']['tools_used'])}")
    print(f"Regeneraciones: {result['trace']['regeneration_count']}")
```

---

## 🧪 Testing del Sistema Autónomo

### Test Rápido

Crea un archivo `test_autonomous.py`:

```python
"""Test rápido del sistema autónomo."""
from src.agents import AutonomousOrchestrator

def test_sistema_autonomo():
    print("Inicializando sistema autónomo...")
    orchestrator = AutonomousOrchestrator()
    
    # Test 1: Query clara
    print("\n[TEST 1] Query clara")
    result = orchestrator.process_query("¿Qué es un dinosaurio?")
    assert result['intent'] == 'busqueda'
    assert len(result['response']) > 100
    print(f"✓ Intent correcto: {result['intent']}")
    print(f"✓ Respuesta generada: {len(result['response'])} chars")
    
    # Test 2: Query vaga (debe optimizar)
    print("\n[TEST 2] Query vaga (debe optimizar)")
    result = orchestrator.process_query("dinosaurios")
    assert result['intent'] == 'busqueda'
    # Verificar si se usó optimize_search_query
    tools_used = result['trace'].get('tools_used', [])
    if 'optimize_search_query' in str(tools_used):
        print("✓ Agente decidió optimizar query vaga")
    else:
        print("⚠ Agente no optimizó (puede variar)")
    
    # Test 3: Comparación
    print("\n[TEST 3] Comparación")
    result = orchestrator.process_query("Compara T-Rex con Velociraptor")
    assert result['intent'] == 'comparacion'
    print(f"✓ Clasificado correctamente como: {result['intent']}")
    
    # Test 4: General (sin RAG)
    print("\n[TEST 4] Consulta general")
    result = orchestrator.process_query("Hola, ¿cómo estás?")
    assert result['intent'] == 'general'
    assert result['documents_used'] == 0
    print(f"✓ Sin RAG: {result['documents_used']} docs")
    
    print("\n" + "=" * 80)
    print("✓ TODOS LOS TESTS PASARON")
    print("=" * 80)

if __name__ == "__main__":
    test_sistema_autonomo()
```

Ejecutar:
```bash
python test_autonomous.py
```

---

## 📊 Comparación de Resultados

### Ejecutar Comparación

```python
"""Comparar agentes clásicos vs autónomos."""
import time
from src.agents import Orchestrator, AutonomousOrchestrator

def comparar_sistemas():
    query = "¿Qué es un Tiranosaurio Rex?"
    
    # Sistema clásico
    print("Ejecutando sistema CLÁSICO...")
    start = time.time()
    orchestrator_clasico = Orchestrator()
    result_clasico = orchestrator_clasico.process_query(query)
    tiempo_clasico = time.time() - start
    
    # Sistema autónomo
    print("\nEjecutando sistema AUTÓNOMO...")
    start = time.time()
    orchestrator_autonomo = AutonomousOrchestrator()
    result_autonomo = orchestrator_autonomo.process_query(query)
    tiempo_autonomo = time.time() - start
    
    # Comparación
    print("\n" + "=" * 80)
    print("COMPARACIÓN DE RESULTADOS")
    print("=" * 80)
    
    print(f"\n📊 MÉTRICAS:")
    print(f"  Clásico   → Tiempo: {tiempo_clasico:.2f}s")
    print(f"  Autónomo  → Tiempo: {tiempo_autonomo:.2f}s")
    
    print(f"\n📝 RESPUESTAS:")
    print(f"  Clásico   → {len(result_clasico['response'])} chars")
    print(f"  Autónomo  → {len(result_autonomo['response'])} chars")
    
    print(f"\n🔍 TRAZABILIDAD:")
    print(f"  Clásico   → Trace limitado")
    print(f"  Autónomo  → {len(result_autonomo['trace']['steps'])} pasos")
    print(f"               {len(result_autonomo['trace']['tools_used'])} tools usadas")
    
    print(f"\n✅ VALIDACIÓN:")
    print(f"  Clásico   → Score: {result_clasico['validation']['confidence_score']:.2f}")
    print(f"  Autónomo  → Score: {result_autonomo['validation']['confidence_score']:.2f}")

if __name__ == "__main__":
    comparar_sistemas()
```

---

## 🐛 Troubleshooting

### Error: "Tool X not found"

**Problema:** El agente intenta usar una tool que no está disponible.

**Solución:**
```python
# Verificar que todas las tools están importadas
from src.tools import ALL_LANGCHAIN_TOOLS

print(f"Tools disponibles: {len(ALL_LANGCHAIN_TOOLS)}")
for tool in ALL_LANGCHAIN_TOOLS:
    print(f"  - {tool.name}")
```

### Error: "API key not configured"

**Problema:** LLMs requieren API keys configuradas.

**Solución:**
```bash
# .env
GOOGLE_API_KEY=tu_api_key_gemini
GROQ_API_KEY=tu_api_key_groq
```

### Agente no usa tools esperadas

**Problema:** El agente decide no usar una tool que esperabas.

**Explicación:** Esto es **NORMAL y DESEADO**. Los agentes son autónomos y deciden basándose en contexto.

**Verificación:**
```python
# Ver razonamiento del agente
result = classifier.classify(query)
print(f"Razonamiento: {result['reasoning']}")
print(f"Pasos: {result['intermediate_steps']}")
```

### Tiempos de respuesta lentos

**Problema:** El sistema tarda mucho en responder.

**Causa:** Los agentes autónomos pueden hacer múltiples llamadas a LLMs.

**Solución:**
```python
# Reducir max_iterations en AgentExecutor
self.agent_executor = AgentExecutor(
    agent=self.agent,
    tools=self.tools,
    max_iterations=3,  # Reducir de 5 a 3
    verbose=True
)
```

---

## 📈 Mejoras Graduales

### Fase 1: Probar Sistema Autónomo
```bash
python demo_autonomous_system.py
```
- Familiarízate con el comportamiento
- Observa decisiones de agentes
- Verifica trazabilidad

### Fase 2: Migrar Scripts de Demo
- Actualiza `main.py` a `AutonomousOrchestrator`
- Actualiza `examples.py` a agentes autónomos
- Añade visualización de trazabilidad

### Fase 3: Documentar para Informe
- Usa `INFORME_TEMPLATE_TOOLS_AGENTS.md`
- Documenta al menos 10 casos de uso
- Captura screenshots de trazabilidad

### Fase 4: Preparar Video
- Usa `VIDEO_PITCH_GUIDE.md`
- Practica demos con `demo_autonomous_system.py`
- Graba mostrando autonomía real

---

## ✅ Checklist de Integración

### Código
- [ ] `src/tools/__init__.py` actualizado con nuevas tools
- [ ] `src/agents/__init__.py` actualizado con agentes autónomos
- [ ] Agentes autónomos creados y funcionales
- [ ] Tools con `@tool` implementadas

### Testing
- [ ] `test_autonomous.py` ejecutado exitosamente
- [ ] Comparación clásico vs autónomo realizada
- [ ] Demos del script funcionando

### Documentación
- [ ] `AUTONOMOUS_AGENTS_GUIDE.md` revisado
- [ ] `INFORME_TEMPLATE_TOOLS_AGENTS.md` adaptado
- [ ] Casos de uso documentados (min 10)

### Demo
- [ ] `demo_autonomous_system.py` funcional
- [ ] Queries de demo preparadas
- [ ] Screenshots de trazabilidad capturadas

### Video
- [ ] `VIDEO_PITCH_GUIDE.md` leído
- [ ] Guion preparado
- [ ] Demos ensayadas

---

## 🎯 Próximos Pasos

1. **Ejecutar Demo:**
   ```bash
   python demo_autonomous_system.py
   ```

2. **Probar Diferentes Queries:**
   - Query clara: "¿Qué es un T-Rex?"
   - Query vaga: "dinosaurios"
   - Comparación: "Compara carnívoros con herbívoros"
   - Resumen: "Resume información sobre fósiles"
   - General: "Hola"

3. **Analizar Trazabilidad:**
   - Ver qué tools usó cada agente
   - Identificar decisiones autónomas
   - Verificar adaptación contextual

4. **Documentar Casos de Uso:**
   - Capturar al menos 10 escenarios
   - Screenshot de cada flujo
   - Explicar decisiones de agentes

5. **Preparar Video:**
   - Seleccionar mejores demos
   - Escribir guion basado en `VIDEO_PITCH_GUIDE.md`
   - Practicar narración

---

## 📞 Soporte

Si encuentras problemas:

1. **Revisa logs:** Los agentes autónomos generan logs detallados
2. **Verifica API keys:** Gemini y Groq deben estar configurados
3. **Consulta documentación:** `AUTONOMOUS_AGENTS_GUIDE.md`
4. **Analiza trazabilidad:** `result['trace']` tiene información detallada

---

**¡Éxito con tu Sistema Agentic AI Autónomo!** 🚀
