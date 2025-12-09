# Sistema Agentic AI Autónomo con Tools

## 🎯 Arquitectura del Sistema

El sistema ahora está compuesto por **agentes verdaderamente autónomos** que utilizan **LangChain Tools** para tomar decisiones y ejecutar acciones de forma independiente.

### Agentes Autónomos

#### 1. **AutonomousClassifierAgent**
- **Responsabilidad**: Clasificar la intención del usuario
- **LLM**: Gemini 2.5 Flash (comprensión contextual profunda)
- **Tools Disponibles**:
  - `classify_intent`: Clasificación con LLM especializado
  - `get_available_documents_info`: Verificar documentos disponibles
  - `log_agent_decision`: Registrar decisiones
- **Autonomía**: Decide cuándo usar cada tool según la complejidad de la consulta

#### 2. **AutonomousRetrieverAgent**
- **Responsabilidad**: Recuperar documentos relevantes
- **LLM**: Groq Llama 3.1 70B (velocidad de recuperación)
- **Tools Disponibles**:
  - `search_documents`: Búsqueda semántica por similitud
  - `search_documents_by_metadata`: Búsqueda por filtros
  - `optimize_search_query`: Optimizar queries vagas
  - `log_agent_action`: Registrar acciones
- **Autonomía**: Determina si optimizar la query, cuántos documentos recuperar, y si hacer múltiples búsquedas

#### 3. **AutonomousRAGAgent**
- **Responsabilidad**: Generar respuestas contextuales
- **LLM**: Groq Llama 3.1 70B (generación rápida)
- **Tools Disponibles**:
  - `generate_rag_response`: Respuesta con documentos
  - `generate_general_response`: Respuesta sin documentos
  - `log_agent_action`: Registrar acciones
- **Autonomía**: Decide qué tipo de respuesta generar según contexto y adapta el estilo a la intención

#### 4. **AutonomousCriticAgent**
- **Responsabilidad**: Validar calidad de respuestas
- **LLM**: Gemini 2.5 Flash (razonamiento profundo)
- **Tools Disponibles**:
  - `validate_response`: Validación multi-criterio completa
  - `check_hallucination`: Detección de alucinaciones
  - `log_agent_decision`: Registrar decisiones
- **Autonomía**: Decide cuándo hacer análisis profundo de alucinaciones y cuándo aprobar/rechazar respuestas

---

## 🛠️ Tools de LangChain

### Categoría: Búsqueda y Recuperación

#### `search_documents(query, k, score_threshold)`
Busca documentos en el vector store por similitud semántica.

**Cuándo usarla**:
- Usuario busca información específica
- Se necesita contexto para generar respuesta
- Búsqueda, resumen o comparación

**Parámetros**:
- `query`: Consulta en lenguaje natural
- `k`: Número de documentos (3-10 según intención)
- `score_threshold`: Umbral de relevancia (0.0-1.0)

**Retorna**: Lista de documentos con content, metadata, score

---

#### `search_documents_by_metadata(metadata_filter, k)`
Busca documentos filtrando por metadatos específicos.

**Cuándo usarla**:
- Usuario menciona un documento específico por nombre
- Se necesita buscar en archivo particular
- Filtrar por autor, fecha, etc.

**Parámetros**:
- `metadata_filter`: Dict con filtros (ej: `{"source": "doc.pdf"}`)
- `k`: Número máximo de documentos

**Retorna**: Lista de documentos que coinciden

---

#### `optimize_search_query(query, intent)`
Optimiza una consulta para mejorar recuperación.

**Cuándo usarla**:
- Query vaga o ambigua
- Query muy corta (< 5 palabras)
- Se quiere expandir con sinónimos

**Parámetros**:
- `query`: Consulta original
- `intent`: Tipo de intención (busqueda/resumen/comparacion)

**Retorna**: Query optimizada expandida

**Ejemplo**:
```
Input: "diabetes"
Output: "diabetes mellitus tipo 1 tipo 2 síntomas tratamiento glucosa"
```

---

### Categoría: Generación de Respuestas

#### `generate_rag_response(query, documents, intent)`
Genera respuesta basada en documentos recuperados (RAG).

**Cuándo usarla**:
- Hay documentos relevantes disponibles
- Se necesita respuesta con citas
- Intent requiere RAG (busqueda/resumen/comparacion)

**Parámetros**:
- `query`: Pregunta del usuario
- `documents`: Lista de docs con content y metadata
- `intent`: Adapta estilo (busqueda/resumen/comparacion)

**Retorna**: Respuesta con citas [Fuente X]

---

#### `generate_general_response(query)`
Genera respuesta conversacional sin documentos.

**Cuándo usarla**:
- Consulta conversacional (saludos)
- No requiere información de documentos
- Intent = "general"

**Parámetros**:
- `query`: Consulta del usuario

**Retorna**: Respuesta directa del LLM

---

### Categoría: Validación

#### `validate_response(query, response, context_documents)`
Validación completa de respuesta contra fuentes.

**Cuándo usarla**:
- Después de generar respuesta RAG
- Control de calidad obligatorio
- Antes de entregar respuesta al usuario

**Parámetros**:
- `query`: Pregunta original
- `response`: Respuesta generada
- `context_documents`: Docs usados para generar

**Retorna**:
```python
{
    "is_valid": bool,
    "confidence_score": float,  # 0-1
    "issues": List[str],
    "recommendations": str
}
```

**Criterios evaluados**:
1. Coherencia estructural (20%)
2. Alineación con fuentes (30%)
3. Ausencia de alucinaciones (25%)
4. Completitud (15%)
5. Calidad de citas (10%)

---

#### `check_hallucination(response, context_documents)`
Análisis específico de alucinaciones.

**Cuándo usarla**:
- validate_response detectó problemas
- Se necesita análisis profundo
- Dudas sobre fidelidad a fuentes

**Parámetros**:
- `response`: Respuesta a verificar
- `context_documents`: Documentos fuente

**Retorna**:
```python
{
    "has_hallucination": bool,
    "hallucination_score": float,  # 0=sin, 1=graves
    "problematic_claims": List[str],
    "analysis": str
}
```

---

### Categoría: Clasificación

#### `classify_intent(query)`
Clasifica intención del usuario en 4 categorías.

**Cuándo usarla**:
- Primera etapa de procesamiento
- Consulta nueva del usuario
- Determinar estrategia de respuesta

**Parámetros**:
- `query`: Consulta en lenguaje natural

**Retorna**:
```python
{
    "intent": str,  # busqueda/resumen/comparacion/general
    "confidence": float,  # 0-1
    "requires_rag": bool,
    "reasoning": str
}
```

**Categorías**:
- **busqueda**: Información específica de documentos
- **resumen**: Sintetizar documentos
- **comparacion**: Contrastar conceptos
- **general**: Conversación sin RAG

---

### Categoría: Logging y Trazabilidad

#### `log_agent_decision(agent_name, decision, reasoning, metadata)`
Registra decisiones de agentes para trazabilidad.

**Cuándo usarla**:
- Agente toma decisión importante
- Se necesita auditar comportamiento
- Crear historial de razonamiento

**Parámetros**:
- `agent_name`: Nombre del agente
- `decision`: Decisión tomada
- `reasoning`: Justificación
- `metadata`: Info adicional (opcional)

**Retorna**: Confirmación con timestamp

---

#### `log_agent_action(agent_name, action, input_data, output_data, success)`
Registra acciones ejecutadas por agentes.

**Cuándo usarla**:
- Agente ejecuta acción concreta
- Rastrear flujo de datos
- Debugging y análisis

**Parámetros**:
- `agent_name`: Nombre del agente
- `action`: Acción ejecutada
- `input_data`: Entrada (resumida)
- `output_data`: Salida (resumida)
- `success`: Si fue exitosa (default: True)

**Retorna**: Confirmación con timestamp

---

#### `get_available_documents_info()`
Información sobre documentos indexados.

**Cuándo usarla**:
- Usuario pregunta qué hay disponible
- Verificar si sistema tiene contenido
- Info sobre el corpus

**Retorna**:
```python
{
    "total_documents": int,
    "status": str,
    "message": str
}
```

---

## 📊 Flujo del Sistema Autónomo

```
Usuario → "¿Qué es la diabetes tipo 2?"
    ↓
[1] ClassifierAgent (con tools)
    → classify_intent("¿Qué es la diabetes tipo 2?")
    → log_agent_decision(...)
    ↓ intent="busqueda", requires_rag=True
    
[2] RetrieverAgent (con tools)
    → optimize_search_query(query, "busqueda")  [decide si necesario]
    → search_documents(query_optimizada, k=4)
    → log_agent_action(...)
    ↓ 4 documentos recuperados
    
[3] RAGAgent (con tools)
    → generate_rag_response(query, docs, "busqueda")
    → log_agent_action(...)
    ↓ Respuesta generada con citas
    
[4] CriticAgent (con tools)
    → validate_response(query, response, docs)
    → check_hallucination(response, docs)  [si hay dudas]
    → log_agent_decision(...)
    ↓ 
    - Si válida → Entregar respuesta
    - Si inválida → Regenerar (max 2 veces)
    
Usuario ← Respuesta final + trazabilidad completa
```

---

## 🔧 Uso de los Agentes Autónomos

### Ejemplo 1: Uso Básico

```python
from src.agents.autonomous_orchestrator import AutonomousOrchestrator

# Inicializar orquestador (carga todos los agentes)
orchestrator = AutonomousOrchestrator()

# Procesar consulta (agentes deciden qué tools usar)
result = orchestrator.process_query("¿Qué es el COVID-19?")

print(result["response"])
print(f"Intención: {result['intent']}")
print(f"Documentos usados: {result['documents_used']}")
print(f"Validación: {result['validation']['confidence_score']:.2f}")
print(f"Tools usadas: {result['trace']['tools_used']}")
```

### Ejemplo 2: Uso Individual de Agentes

```python
from src.agents.autonomous_classifier_agent import AutonomousClassifierAgent

# Agente individual (decide cuándo usar tools)
classifier = AutonomousClassifierAgent()

# El agente analiza y decide si usar classify_intent tool
classification = classifier.classify("Compara diabetes tipo 1 y 2")

print(f"Intención: {classification['intent']}")
print(f"Razonamiento: {classification['reasoning']}")
print(f"Pasos intermedios: {len(classification['intermediate_steps'])}")
```

### Ejemplo 3: Trazabilidad Completa

```python
result = orchestrator.process_query("Resume el artículo sobre diabetes")

# Ver todos los pasos
for step in result["trace"]["steps"]:
    print(f"Paso {step['step']}: {step['agent']} - {step['action']}")
    print(f"  Resultado: {step['result']}")

# Ver agentes llamados
print(f"Agentes: {result['trace']['agents_called']}")

# Ver tools usadas
print(f"Tools: {result['trace']['tools_used']}")
```

---

## 🎓 Ventajas del Sistema Autónomo

### ✅ Antes (Sistema Guiado)
- Código Python decide cada paso
- Agentes ejecutan órdenes predefinidas
- Flujo rígido y predecible
- Sin adaptación a contexto

### ✨ Ahora (Sistema Autónomo)
- **Agentes toman decisiones**: Cada agente razona qué hacer
- **Tools bajo demanda**: Usan tools cuando lo necesitan
- **Flujo adaptativo**: Se ajusta al contexto de cada consulta
- **Trazabilidad real**: Se ve exactamente qué decidió cada agente

### Ejemplo de Autonomía

**Query vaga**: "covid"

```
RetrieverAgent decide:
1. "Query muy corta, necesito optimizarla"
2. Usa: optimize_search_query("covid", "busqueda")
3. Query optimizada: "covid-19 coronavirus síntomas tratamiento"
4. Usa: search_documents(query_optimizada, k=4)
5. Registra: log_agent_action(...)
```

**Query clara**: "¿Cuáles son los síntomas del COVID-19?"

```
RetrieverAgent decide:
1. "Query específica y clara, no necesito optimizar"
2. Usa directamente: search_documents(query, k=4)
3. Registra: log_agent_action(...)
```

---

## 📋 Checklist de Implementación

- [x] Convertir tools existentes a formato `@tool` de LangChain
- [x] Crear nuevas tools útiles (11 total)
- [x] Documentación detallada en docstrings de cada tool
- [x] Agente Clasificador Autónomo con tools
- [x] Agente Recuperador Autónomo con tools
- [x] Agente RAG Autónomo con tools
- [x] Agente Crítico Autónomo con tools
- [x] Orquestador que coordina agentes autónomos
- [x] Sistema de trazabilidad completo
- [x] Documentación de tools y agentes

---

## 🚀 Próximos Pasos

1. **Probar el sistema autónomo** con consultas variadas
2. **Ajustar prompts** de agentes según resultados
3. **Agregar más tools** si se identifican necesidades
4. **Optimizar decisiones** de agentes basado en logs
5. **Documentar casos de uso** en informe técnico

---

## 📚 Referencias

- [LangChain Tools Documentation](https://python.langchain.com/docs/modules/tools/)
- [LangChain Agents](https://python.langchain.com/docs/modules/agents/)
- [Tool Calling with Gemini](https://ai.google.dev/gemini-api/docs/function-calling)
- [Groq API Documentation](https://console.groq.com/docs)
