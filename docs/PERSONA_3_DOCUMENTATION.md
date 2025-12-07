# Documentación Técnica - Persona 3

## Recuperación Semántica, RAG y Evaluación de Respuestas

**Implementador**: Persona 3  
**Fecha de implementación**: Diciembre 2025  
**Componentes**: RetrieverAgent, RAGAgent, CriticAgent

---

## Tabla de Contenidos

1. [Visión General](#visión-general)
2. [RetrieverAgent - Recuperación Semántica](#retrieveragent---recuperación-semántica)
3. [RAGAgent - Generación de Respuestas](#ragagent---generación-de-respuestas)
4. [CriticAgent - Validación y Evaluación](#criticagent---validación-y-evaluación)
5. [Ciclo de Realimentación](#ciclo-de-realimentación)
6. [Prompts Especializados](#prompts-especializados)
7. [Proceso de Verificación](#proceso-de-verificación)
8. [Métricas y Evaluación](#métricas-y-evaluación)
9. [Ejemplos de Uso](#ejemplos-de-uso)

---

## Visión General

### Arquitectura del Sistema de Recuperación y Generación

```
Usuario Query
     ↓
[Orchestrator] ← Persona 1
     ↓
[ClassifierAgent] ← Persona 1
     ↓
┌─────────────────────────────────┐
│  PERSONA 3 - IMPLEMENTACIÓN     │
│                                 │
│  ┌──────────────────────────┐  │
│  │ RetrieverAgent           │  │
│  │ - Optimiza query con LLM │  │
│  │ - Consulta FAISS         │  │
│  │ - Rankea resultados      │  │
│  └──────────────────────────┘  │
│             ↓                   │
│  ┌──────────────────────────┐  │
│  │ RAGAgent                 │  │
│  │ - Prompts especializados │  │
│  │ - Genera con contexto    │  │
│  │ - Incluye citas          │  │
│  └──────────────────────────┘  │
│             ↓                   │
│  ┌──────────────────────────┐  │
│  │ CriticAgent              │  │
│  │ - Valida 5 criterios     │  │
│  │ - Detecta alucinaciones  │  │
│  │ - Decide regeneración    │  │
│  └──────────────────────────┘  │
│             ↓                   │
│      ┌─────────────┐            │
│      │ ¿Válida?    │            │
│      └─────────────┘            │
│         /        \              │
│       Sí         No             │
│        |          ↓              │
│        |    Regenerar (max 2x)  │
│        |          │              │
│        └──────────┘              │
└─────────────────────────────────┘
           ↓
    Respuesta Final
```

### Responsabilidades Implementadas

1. **Recuperación Semántica**
   - Optimización de consultas con LLM
   - Consulta inteligente a FAISS
   - Ranking y filtrado por relevancia
   - Métodos especializados por intención

2. **Generación RAG**
   - Prompts especializados (búsqueda, resumen, comparación)
   - Generación con contexto recuperado
   - Inclusión obligatoria de citas
   - Respuestas generales sin RAG

3. **Validación y Crítica**
   - Evaluación multi-criterio (5 criterios)
   - Detección de alucinaciones
   - Score ponderado global
   - Decisión automática de regeneración

4. **Ciclo de Realimentación**
   - Regeneración automática si score insuficiente
   - Máximo 2 intentos
   - Selección de mejor respuesta
   - Historial completo de intentos

---

## RetrieverAgent - Recuperación Semántica

### Archivo
`src/agents/retriever_agent.py`

### Descripción
Agente responsable de recuperar documentos relevantes del vector store FAISS. Optimiza las consultas del usuario mediante LLM antes de la búsqueda semántica.

### Componentes

#### 1. Optimización de Consultas

**Estrategia**:
- Usa Groq (Llama 3.1 70B) para reformular queries
- Expande con sinónimos y términos relacionados
- Elimina ambigüedades
- Extrae keywords principales

**Modelo de datos**:
```python
class OptimizedQuery(BaseModel):
    optimized_query: str  # Query reformulada
    keywords: List[str]   # Palabras clave extraídas
    reasoning: str        # Justificación de cambios
```

**Prompt de optimización**:
```python
"""Eres un experto en optimización de consultas para búsqueda semántica.

OBJETIVOS:
1. Expandir la consulta con sinónimos y términos relacionados
2. Eliminar ambigüedades y palabras no informativas
3. Mantener la intención original del usuario
4. Extraer palabras clave principales

ESTRATEGIAS SEGÚN INTENCIÓN:
- busqueda: Enfocarse en términos específicos y precisos
- resumen: Ampliar a términos más generales del dominio
- comparacion: Incluir ambos conceptos a comparar explícitamente
- general: Mantener la consulta simple
"""
```

#### 2. Método Principal: `retrieve()`

**Firma**:
```python
def retrieve(self, 
            query: str, 
            k: int = 5, 
            optimize: bool = True,
            intent: str = "busqueda",
            score_threshold: Optional[float] = None) -> List[Dict[str, Any]]
```

**Flujo de ejecución**:
1. Optimiza query con LLM (si `optimize=True`)
2. Consulta FAISS vía `vectorstore_manager.similarity_search()`
3. Rankea y filtra por score threshold
4. Retorna documentos ordenados por relevancia

**Ejemplo de uso**:
```python
retriever = RetrieverAgent()

# Búsqueda estándar
docs = retriever.retrieve(
    query="síntomas del COVID-19",
    k=5,
    optimize=True,
    intent="busqueda",
    score_threshold=0.5
)

# Resultado:
# [
#   {
#     'content': '...',
#     'metadata': {'source': 'doc1.pdf', 'chunk_index': 0},
#     'score': 0.87
#   },
#   ...
# ]
```

#### 3. Métodos Especializados

**Para comparaciones** - `retrieve_for_comparison()`:
```python
def retrieve_for_comparison(self, query: str, num_docs: int = 4)
```
- Recupera 4-6 documentos (mayor diversidad)
- Threshold bajo (0.3) para cubrir ambos conceptos
- Optimización enfocada en extraer términos de ambos elementos

**Para resúmenes** - `retrieve_for_summary()`:
```python
def retrieve_for_summary(self, query: str, max_docs: int = 10)
```
- Recupera 8-10 documentos (mayor cobertura)
- Threshold moderado (0.4) para balance calidad/cantidad
- Optimización para términos generales del dominio

#### 4. Ranking y Filtrado

```python
def _rank_and_filter(self, documents, score_threshold)
```
- Filtra documentos por score mínimo (si se especifica)
- Ordena descendentemente por similitud
- Logging de documentos eliminados

### Configuración LLM

**Modelo**: Groq (Llama 3.1 70B)  
**Justificación**: Latencia mínima para optimización rápida  
**Temperatura**: 0.2  
**Max tokens**: 1000

### Dependencias

- Asume que `vectorstore_manager` está implementado (Persona 2)
- No toca la implementación de FAISS
- Solo consulta la interfaz pública del vector store

---

## RAGAgent - Generación de Respuestas

### Archivo
`src/agents/rag_agent.py`

### Descripción
Agente responsable de generar respuestas basadas en el contexto recuperado. Utiliza prompts especializados según la intención clasificada.

### Componentes

#### 1. Inicialización

```python
def __init__(self):
    self.llm = llm_config.get_rag_llm()           # Groq para RAG
    self.general_llm = llm_config.get_general_llm()  # Groq para general
    
    # Prompts especializados
    self.search_prompt = self._create_search_prompt()
    self.summary_prompt = self._create_summary_prompt()
    self.comparison_prompt = self._create_comparison_prompt()
```

#### 2. Prompts Especializados

##### Prompt de Búsqueda

**Objetivo**: Respuestas precisas con citas explícitas

**Características**:
- Respuesta directa y concisa
- Cada afirmación con su cita [Fuente X]
- No inventa información
- Indica claramente si no encuentra la respuesta

**Prompt completo**:
```python
"""Eres un asistente experto en proporcionar información precisa basada en documentos.

INSTRUCCIONES:
1. Responde la pregunta usando ÚNICAMENTE la información del contexto proporcionado
2. Sé preciso y conciso - ve directo al punto
3. SIEMPRE cita las fuentes usando el formato [Fuente X]
4. Si la información no está en el contexto, indica claramente que no se encontró
5. Organiza la respuesta de forma clara y estructurada
6. No inventes ni asumas información no presente en el contexto

FORMATO DE RESPUESTA:
- Respuesta directa a la pregunta
- Cada afirmación debe tener su cita [Fuente X]
- Si hay múltiples fuentes, cítalas todas

EJEMPLO:
"El COVID-19 se transmite principalmente por contacto cercano [Fuente 1]. 
Los síntomas más comunes incluyen fiebre y tos [Fuente 2]."
"""
```

##### Prompt de Resumen

**Objetivo**: Síntesis estructurada de información clave

**Características**:
- Identifica puntos clave de múltiples documentos
- Organización con viñetas/numeración
- Elimina redundancias
- Cita fuentes de cada punto

**Estructura recomendada**:
1. Introducción breve del tema
2. Puntos clave principales (3-5)
3. Detalles relevantes de cada punto
4. Conclusión o síntesis final

**Prompt completo**:
```python
"""Eres un asistente experto en sintetizar información de múltiples documentos.

INSTRUCCIONES:
1. Lee todos los documentos del contexto proporcionado
2. Identifica y extrae los puntos clave más importantes
3. Organiza la información de forma lógica y estructurada
4. Usa viñetas o numeración para mayor claridad
5. Cita las fuentes de cada punto clave [Fuente X]
6. Elimina redundancias entre documentos
7. Mantén un tono objetivo y profesional

ESTRUCTURA RECOMENDADA:
- Introducción breve del tema
- Puntos clave principales (3-5)
- Detalles relevantes de cada punto
- Conclusión o síntesis final
"""
```

##### Prompt de Comparación

**Objetivo**: Análisis contrastivo claro y equilibrado

**Características**:
- Identifica elementos a comparar
- Destaca similitudes Y diferencias
- Formato estructurado (tabla o puntos)
- Objetivo sin sesgos

**Estructura recomendada**:
1. Breve descripción de cada elemento
2. Similitudes entre ambos
3. Diferencias clave (punto por punto)
4. Conclusión comparativa

**Prompt completo**:
```python
"""Eres un asistente experto en análisis comparativo de conceptos.

INSTRUCCIONES:
1. Identifica los elementos a comparar en la pregunta
2. Analiza el contexto para extraer información de cada elemento
3. Organiza la comparación de forma estructurada
4. Destaca similitudes Y diferencias de forma equilibrada
5. Usa tabla o formato punto por punto para claridad
6. Cita las fuentes para cada elemento comparado [Fuente X]
7. Sé objetivo y evita sesgos

FORMATO DE COMPARACIÓN:
**Elemento A:**
- Característica 1 [Fuente X]
- Característica 2 [Fuente Y]

**Elemento B:**
- Característica 1 [Fuente Z]
- Característica 2 [Fuente W]
"""
```

#### 3. Método Principal: `generate_response()`

**Firma**:
```python
def generate_response(self, 
                     query: str, 
                     documents: List[Dict[str, Any]], 
                     intent: str = "busqueda") -> Dict[str, Any]
```

**Flujo de ejecución**:
1. Selecciona prompt según intención
2. Formatea contexto de documentos
3. Invoca LLM (Groq) para generar respuesta
4. Extrae fuentes utilizadas
5. Retorna respuesta estructurada

**Retorno**:
```python
{
    "response": "...",           # Respuesta generada
    "sources": [...],            # Lista de fuentes
    "intent": "busqueda",        # Intención usada
    "num_documents_used": 5      # Cantidad de docs
}
```

#### 4. Formateo de Contexto

```python
def _format_context(self, documents: List[Dict[str, Any]]) -> str
```

**Formato**:
```
[Fuente 1] (De: documento1.pdf)
Contenido del fragmento 1...

---

[Fuente 2] (De: documento2.pdf)
Contenido del fragmento 2...

---
...
```

#### 5. Respuestas Generales (sin RAG)

```python
def generate_general_response(self, query: str) -> str
```

**Uso**: Para consultas conversacionales, saludos, preguntas generales

**Características**:
- No requiere documentos del vector store
- Temperatura más alta (0.5) para naturalidad
- Prompt simple y conversacional
- Indica si necesita información específica

#### 6. Formateo Final con Fuentes

```python
def format_response_with_sources(self, response_data: Dict[str, Any]) -> str
```

**Añade sección**:
```
--- Fuentes consultadas ---
• Fuente 1: documento1.pdf (Fragmento 0)
• Fuente 2: documento2.pdf (Fragmento 3)
• Fuente 3: documento3.html (Fragmento 1)
```

### Configuración LLM

**Modelo**: Groq (Llama 3.1 70B)  
**Justificación**: Velocidad de generación con baja latencia  
**Temperatura RAG**: 0.3 (balance creatividad/precisión)  
**Temperatura General**: 0.5 (naturalidad conversacional)  
**Max tokens**: 2000 (RAG), 1500 (General)

### Ejemplo de Uso Completo

```python
rag_agent = RAGAgent()

# Generar respuesta con RAG
response_data = rag_agent.generate_response(
    query="¿Cuáles son los síntomas del COVID-19?",
    documents=retrieved_docs,
    intent="busqueda"
)

# Formatear con fuentes
formatted = rag_agent.format_response_with_sources(response_data)

print(formatted)
# Salida:
# Los síntomas más comunes del COVID-19 incluyen fiebre [Fuente 1],
# tos seca [Fuente 1, 2], y fatiga [Fuente 2]...
# 
# --- Fuentes consultadas ---
# • Fuente 1: covid_info.pdf (Fragmento 0)
# • Fuente 2: sintomas.html (Fragmento 2)
```

---

## CriticAgent - Validación y Evaluación

### Archivo
`src/agents/critic_agent.py`

### Descripción
Agente responsable de validar respuestas generadas mediante evaluación multi-criterio. Detecta alucinaciones, verifica coherencia y decide si regenerar.

### Componentes

#### 1. Modelo de Validación

```python
class ValidationCriteria(BaseModel):
    # Scores numéricos (0-1)
    coherence_score: float
    alignment_score: float
    hallucination_score: float
    completeness_score: float
    citation_score: float
    
    # Justificaciones
    coherence_reasoning: str
    alignment_reasoning: str
    hallucination_reasoning: str
    completeness_reasoning: str
    citation_reasoning: str
    
    # Decisión
    overall_assessment: str
    needs_regeneration: bool
    specific_issues: List[str]
```

#### 2. Sistema de Evaluación Multi-Criterio

##### Criterio 1: Coherencia (20%)

**Evalúa**:
- Estructura lógica y organización
- Fluidez entre ideas
- Facilidad de comprensión

**Penaliza**:
- Incoherencias y contradicciones
- Saltos lógicos sin conexión
- Redundancias innecesarias

**Score**:
- 1.0: Perfecto flujo lógico
- 0.5: Algunas inconsistencias
- 0.0: Incoherente o confuso

##### Criterio 2: Alineación (30%) - PESO MÁS ALTO

**Evalúa**:
- Fidelidad al contexto proporcionado
- Uso correcto de información fuente
- Interpretaciones precisas

**Penaliza**:
- Distorsión de información
- Interpretaciones incorrectas
- Desviación del contexto

**Score**:
- 1.0: Totalmente alineado con contexto
- 0.5: Parcialmente alineado
- 0.0: No alineado o contradice contexto

**Threshold crítico**: 0.60

##### Criterio 3: Alucinaciones (25%) - CRÍTICO

**Evalúa**:
- Ausencia de información inventada
- Todas las afirmaciones respaldadas
- No inferencias sin fundamento

**Penaliza**:
- Cualquier afirmación no presente en contexto
- Estadísticas inventadas
- "Hechos" sin respaldo

**Score**:
- 1.0: Sin alucinaciones (toda info está en contexto)
- 0.7: Algunas inferencias razonables
- 0.5: Inferencias no respaldadas
- 0.0: Información claramente inventada

**Threshold crítico**: 0.70

##### Criterio 4: Completitud (15%)

**Evalúa**:
- Responde completamente la pregunta
- Cubre todos los aspectos solicitados
- Nivel de detalle adecuado

**Penaliza**:
- Respuestas parciales
- Omisión de información relevante disponible
- Superficialidad excesiva

**Score**:
- 1.0: Respuesta completa y detallada
- 0.5: Respuesta parcial
- 0.0: No responde la pregunta

##### Criterio 5: Citas (10%)

**Evalúa**:
- Presencia de referencias [Fuente X]
- Apropiado uso de citas
- Cobertura de afirmaciones importantes

**Penaliza**:
- Ausencia de citas
- Citas incorrectas o inexistentes
- Afirmaciones sin respaldo

**Score**:
- 1.0: Todas las afirmaciones citadas correctamente
- 0.5: Algunas citas presentes
- 0.0: Sin citas o todas incorrectas

#### 3. Cálculo de Score Global

**Fórmula**:
```python
score_global = (
    coherence_score * 0.20 +
    alignment_score * 0.30 +
    hallucination_score * 0.25 +
    completeness_score * 0.15 +
    citation_score * 0.10
)
```

**Pesos justificados**:
- **Alineación (30%)**: Más importante - fidelidad al contexto
- **Alucinaciones (25%)**: Crítico - confiabilidad del sistema
- **Coherencia (20%)**: Importante - calidad de respuesta
- **Completitud (15%)**: Relevante - utilidad al usuario
- **Citas (10%)**: Deseable - transparencia

#### 4. Decisión de Regeneración

**Se regenera si**:
```python
needs_regeneration = (
    llm_decision OR
    overall_score < 0.65 OR
    hallucination_score < 0.70 OR
    alignment_score < 0.60
)
```

**Thresholds**:
- Score global mínimo: **0.65**
- Alucinaciones mínimo: **0.70** (crítico)
- Alineación mínimo: **0.60** (crítico)

#### 5. Prompt de Validación

**Prompt completo**:
```python
"""Eres un evaluador experto de respuestas RAG. Tu tarea es validar respuestas 
generadas por sistemas de IA de forma rigurosa y objetiva.

CRITERIOS DE EVALUACIÓN (cada uno con score 0-1):

1. COHERENCIA (0-1): Evalúa la estructura lógica y fluidez
   - ¿La respuesta está bien organizada?
   - ¿Las ideas fluyen de forma lógica?
   - ¿Es fácil de entender?
   Penaliza: Incoherencias, saltos lógicos, redundancias

2. ALINEACIÓN (0-1): Evalúa fidelidad al contexto proporcionado
   - ¿Cada afirmación está respaldada por el contexto?
   - ¿Se usa correctamente la información del contexto?
   - ¿Se mantiene fiel a los documentos fuente?
   Penaliza: Interpretaciones incorrectas, distorsión de información

3. ALUCINACIONES (0-1): Detecta información inventada
   - 1.0 = Sin alucinaciones (toda la info está en el contexto)
   - 0.5 = Algunas inferencias no respaldadas
   - 0.0 = Información inventada o falsa
   CRÍTICO: Cualquier afirmación no presente en el contexto es alucinación

4. COMPLETITUD (0-1): Evalúa si responde completamente
   - ¿Se responde la pregunta del usuario?
   - ¿Se cubren todos los aspectos solicitados?
   - ¿La respuesta es suficientemente detallada?
   Penaliza: Respuestas parciales, omisión de información relevante

5. CITAS (0-1): Evalúa calidad de referencias
   - ¿Están presentes las citas [Fuente X]?
   - ¿Las citas son apropiadas y precisas?
   - ¿Cada afirmación importante tiene su cita?
   Penaliza: Ausencia de citas, citas incorrectas

DECISIÓN DE REGENERACIÓN:
Marca needs_regeneration=True si:
- Score de alucinaciones < 0.7 (problema crítico)
- Score de alineación < 0.6 (problema crítico)
- Score global < 0.65
- Hay problemas graves listados en specific_issues
"""
```

#### 6. Método Principal: `validate()`

**Firma**:
```python
def validate(self, 
            query: str, 
            response: str, 
            context_docs: List[Dict[str, Any]]) -> Dict[str, Any]
```

**Flujo**:
1. Formatea contexto para validación
2. Invoca Gemini para evaluar 5 criterios
3. Calcula score global ponderado
4. Verifica thresholds críticos
5. Retorna validación estructurada

**Retorno**:
```python
{
    "is_valid": bool,              # Si es aceptable
    "overall_score": float,        # Score global 0-1
    "needs_regeneration": bool,    # Si debe regenerarse
    "criteria_scores": {           # Scores individuales
        "coherence": 0.85,
        "alignment": 0.90,
        "hallucination": 0.95,
        "completeness": 0.80,
        "citation": 0.75
    },
    "feedback": {                  # Justificaciones
        "coherence": "...",
        "alignment": "...",
        ...
    },
    "issues": [...]               # Problemas específicos
}
```

### Configuración LLM

**Modelo**: Gemini 2.5 Flash  
**Justificación**: Razonamiento profundo para validación compleja  
**Temperatura**: 0.1 (evaluación estricta y consistente)  
**Max tokens**: 1500

---

## Ciclo de Realimentación

### Método: `validate_with_regeneration()`

**Archivo**: `src/agents/critic_agent.py`

### Descripción
Implementa el ciclo completo de validación-regeneración con límite de intentos.

### Firma

```python
def validate_with_regeneration(self, 
                               query: str, 
                               response: str,
                               context_docs: List[Dict[str, Any]],
                               regenerate_callback: Callable,
                               max_attempts: int = 2) -> Dict[str, Any]
```

### Flujo de Ejecución

```
┌─────────────────────────────────────┐
│ Intento 1: Respuesta inicial        │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ Validar con 5 criterios             │
│ - Coherencia                        │
│ - Alineación                        │
│ - Alucinaciones                     │
│ - Completitud                       │
│ - Citas                             │
└─────────────────────────────────────┘
              ↓
        ┌─────────────┐
        │ ¿Válida?    │
        └─────────────┘
         /          \
       Sí           No
        |            ↓
        |    ┌──────────────────────┐
        |    │ ¿Quedan intentos?    │
        |    └──────────────────────┘
        |         /          \
        |       Sí           No
        |        ↓            ↓
        |  ┌──────────┐  ┌─────────────────┐
        |  │ Regenerar│  │ Seleccionar      │
        |  │ respuesta│  │ mejor intento    │
        |  └──────────┘  └─────────────────┘
        |        ↓             ↓
        |  ┌──────────────────────┐
        |  │ Intento 2: Nueva     │
        |  │ respuesta generada   │
        |  └──────────────────────┘
        |        ↓
        |  Volver a validar
        |        ↓
        └────────┘
              ↓
┌─────────────────────────────────────┐
│ Retornar mejor respuesta            │
│ + Historial completo                │
└─────────────────────────────────────┘
```

### Parámetros

**`regenerate_callback`**: Función que regenera respuesta
```python
# Firma esperada:
def callback(query: str, 
             context_docs: List[Dict], 
             intent: str) -> Dict[str, Any]:
    return rag_agent.generate_response(query, context_docs, intent)
```

**`max_attempts`**: Máximo número de intentos (default: 2)
- Intento 1: Respuesta inicial
- Intento 2: Primera regeneración (si necesario)
- Total máximo: 2 intentos

### Lógica de Regeneración

```python
# Intento 1
validation = validate(query, response, context_docs)

if not validation["needs_regeneration"]:
    return {status: "validated", attempts: 1}

# Intento 2 (si es necesario)
if attempt < max_attempts:
    new_response = regenerate_callback(query, context_docs, intent)
    validation = validate(query, new_response, context_docs)
    
    if not validation["needs_regeneration"]:
        return {status: "regenerated", attempts: 2}

# Si se alcanza max_attempts sin validar
best_response = max(history, key=lambda x: x["validation"]["overall_score"])
return {status: "max_attempts_reached", best_attempt: X}
```

### Retorno

```python
{
    "final_response": str,         # Mejor respuesta obtenida
    "validation": Dict,            # Validación de respuesta final
    "attempts": int,               # Número de intentos realizados
    "status": str,                 # validated | regenerated | max_attempts_reached
    "history": List[Dict],         # Historial de todos los intentos
    "best_attempt": int            # Número del mejor intento (si aplica)
}
```

### Ejemplo de Uso

```python
critic = CriticAgent()
rag_agent = RAGAgent()

# Callback de regeneración
def regenerate(query, docs, intent):
    return rag_agent.generate_response(query, docs, intent)

# Validar con ciclo de regeneración
result = critic.validate_with_regeneration(
    query="¿Qué es el COVID-19?",
    response=initial_response,
    context_docs=retrieved_docs,
    regenerate_callback=regenerate,
    max_attempts=2
)

print(f"Status: {result['status']}")
print(f"Intentos: {result['attempts']}")
print(f"Score final: {result['validation']['overall_score']}")
print(f"Respuesta: {result['final_response']}")

# Posible salida:
# Status: regenerated
# Intentos: 2
# Score final: 0.78
# Respuesta: El COVID-19 es una enfermedad respiratoria... [Fuente 1]
```

### Historial de Intentos

Cada entrada en `history` contiene:
```python
{
    "attempt": 1,
    "response": "...",
    "validation": {
        "is_valid": False,
        "overall_score": 0.58,
        "needs_regeneration": True,
        "issues": [
            "Ausencia de citas en varias afirmaciones",
            "Score de alucinaciones bajo (0.65)"
        ]
    }
}
```

---

## Prompts Especializados

### Resumen de Todos los Prompts

| Componente | Prompt | Objetivo | Temperatura |
|------------|--------|----------|-------------|
| RetrieverAgent | Optimización de query | Reformular para mejor recuperación | 0.2 |
| RAGAgent | Búsqueda | Respuestas precisas con citas | 0.3 |
| RAGAgent | Resumen | Síntesis estructurada | 0.3 |
| RAGAgent | Comparación | Análisis contrastivo | 0.3 |
| RAGAgent | General | Conversación natural | 0.5 |
| CriticAgent | Validación | Evaluación multi-criterio | 0.1 |

### Principios de Diseño de Prompts

1. **Claridad**: Instrucciones explícitas y sin ambigüedades
2. **Ejemplos**: Incluir ejemplos del formato esperado
3. **Restricciones**: Límites claros (solo contexto, siempre citar)
4. **Estructura**: Formato de salida definido
5. **Penalizaciones**: Qué evitar explícitamente

### Mejores Prácticas Aplicadas

- **Sistema de roles**: "Eres un experto en..."
- **Listas numeradas**: Para instrucciones múltiples
- **Formato visual**: Secciones separadas claramente
- **Ejemplos concretos**: Mostrar salida esperada
- **Énfasis**: MAYÚSCULAS para puntos críticos
- **Estratificación**: Instrucciones generales → específicas

---

## Proceso de Verificación

### Flujo Completo de Verificación

```
1. GENERACIÓN
   ↓
   RAGAgent.generate_response()
   - Selecciona prompt según intención
   - Genera con contexto
   - Incluye citas
   ↓
2. VALIDACIÓN INICIAL
   ↓
   CriticAgent.validate()
   - Evalúa 5 criterios
   - Calcula score global
   - Detecta problemas
   ↓
3. DECISIÓN
   ↓
   ┌─────────────┐
   │ Score ≥ 0.65│
   │ Hal ≥ 0.70  │  → Sí → ACEPTAR
   │ Ali ≥ 0.60  │
   └─────────────┘
        ↓ No
4. REGENERACIÓN (si quedan intentos)
   ↓
   RAGAgent.generate_response()
   - Misma query y contexto
   - Nueva generación
   ↓
   Volver a paso 2
   ↓
5. SELECCIÓN FINAL
   ↓
   - Si validó: usar última respuesta
   - Si max_attempts: usar mejor score
```

### Verificación por Criterio

#### Coherencia
**Verifica**:
- Transiciones lógicas entre párrafos
- Orden de información sensato
- Sin contradicciones internas

**Método**:
- Análisis estructural por Gemini
- Detección de saltos lógicos
- Evaluación de fluidez

#### Alineación
**Verifica**:
- Cada afirmación presente en contexto
- Interpretación correcta de información
- Fidelidad a documentos fuente

**Método**:
- Comparación afirmación por afirmación
- Verificación de interpretaciones
- Detección de distorsiones

#### Alucinaciones
**Verifica**:
- Información inventada
- Estadísticas no presentes
- Afirmaciones sin respaldo

**Método**:
- Búsqueda de cada claim en contexto
- Verificación de números/datos
- Detección de inferencias sin fundamento

#### Completitud
**Verifica**:
- Aspectos de la pregunta cubiertos
- Nivel de detalle suficiente
- Información relevante incluida

**Método**:
- Análisis de cobertura de query
- Evaluación de profundidad
- Detección de omisiones

#### Citas
**Verifica**:
- Presencia de [Fuente X]
- Correctitud de referencias
- Cobertura de afirmaciones

**Método**:
- Detección de patrón [Fuente X]
- Conteo de citas vs afirmaciones
- Verificación de existencia de fuentes

### Logging y Trazabilidad

Cada paso genera logs:
```python
# Ejemplo de logs generados
INFO: Validando respuesta - Query: '¿Qué es el COVID-19?'...
INFO: Usando prompt de BÚSQUEDA
INFO: Invocando Gemini para evaluación
INFO: Score calculado: 0.78
INFO: Criterios: coherence=0.85, alignment=0.90, hallucination=0.75...
WARNING: Score de alucinaciones bajo threshold (0.75 < 0.70)
INFO: Regeneración NO requerida (score global 0.78 > 0.65)
INFO: Validación completada - Valid: True
```

---

## Métricas y Evaluación

### Métricas por Componente

#### RetrieverAgent

**Métricas de recuperación**:
- Documentos recuperados vs solicitados
- Score promedio de similitud
- Documentos filtrados por threshold
- Tiempo de optimización de query
- Tiempo de búsqueda FAISS

**Logging**:
```python
logger.info(f"Vector store retornó {len(documents)} documentos")
logger.info(f"Filtrados {len(documents) - len(filtered_docs)} docs por threshold")
logger.info(f"Recuperación completada: {len(ranked_docs)} documentos finales")
```

#### RAGAgent

**Métricas de generación**:
- Longitud de respuesta (caracteres)
- Número de fuentes citadas
- Tiempo de generación
- Intent usado
- Documentos utilizados

**Logging**:
```python
logger.info(f"Generando respuesta RAG - Intent: {intent}, Docs: {len(documents)}")
logger.info(f"Usando prompt de RESUMEN")
logger.info(f"Respuesta generada exitosamente - Longitud: {len(response_text)} chars")
```

#### CriticAgent

**Métricas de validación**:
- Score global (0-1)
- Scores por criterio (5 valores)
- Número de problemas detectados
- Tiempo de validación
- Decisión de regeneración

**Ejemplo de resultado**:
```python
{
    "overall_score": 0.78,
    "criteria_scores": {
        "coherence": 0.85,
        "alignment": 0.90,
        "hallucination": 0.75,
        "completeness": 0.80,
        "citation": 0.60
    },
    "issues": [
        "Algunas afirmaciones sin cita",
        "Score de citas bajo"
    ]
}
```

### Métricas del Ciclo Completo

**Por consulta**:
- Intentos de generación (1-2)
- Score inicial vs final
- Mejora por regeneración
- Tiempo total de procesamiento
- Estado final (validated/regenerated/max_attempts)

**Ejemplo**:
```python
{
    "attempts": 2,
    "initial_score": 0.58,
    "final_score": 0.78,
    "improvement": +0.20,
    "status": "regenerated",
    "total_time": 8.5  # segundos
}
```

### Métricas Agregadas

Disponibles vía sistema de trazabilidad:
- Tasa de validación en primer intento
- Tasa de regeneración necesaria
- Score promedio por intención
- Problemas más frecuentes
- Tiempo promedio por componente

---

## Ejemplos de Uso

### Ejemplo 1: Búsqueda Simple

```python
from src.agents.retriever_agent import RetrieverAgent
from src.agents.rag_agent import RAGAgent
from src.agents.critic_agent import CriticAgent

# Inicializar agentes
retriever = RetrieverAgent()
rag_agent = RAGAgent()
critic = CriticAgent()

# Consulta
query = "¿Cuáles son los síntomas del COVID-19?"

# 1. Recuperar documentos
docs = retriever.retrieve(
    query=query,
    k=5,
    optimize=True,
    intent="busqueda"
)

print(f"Recuperados: {len(docs)} documentos")

# 2. Generar respuesta
response_data = rag_agent.generate_response(
    query=query,
    documents=docs,
    intent="busqueda"
)

print(f"Respuesta generada: {response_data['response'][:100]}...")

# 3. Validar
validation = critic.validate(
    query=query,
    response=response_data['response'],
    context_docs=docs
)

print(f"Score: {validation['overall_score']}")
print(f"Válida: {validation['is_valid']}")
```

### Ejemplo 2: Resumen con Validación

```python
# Consulta de resumen
query = "Resume la información sobre tratamientos para COVID-19"

# 1. Recuperar más documentos para resumen
docs = retriever.retrieve_for_summary(query, max_docs=10)

# 2. Generar resumen
response_data = rag_agent.generate_response(
    query=query,
    documents=docs,
    intent="resumen"
)

# 3. Validar con ciclo de regeneración
def regenerate(q, d, i):
    return rag_agent.generate_response(q, d, i)

result = critic.validate_with_regeneration(
    query=query,
    response=response_data['response'],
    context_docs=docs,
    regenerate_callback=regenerate,
    max_attempts=2
)

print(f"Status: {result['status']}")
print(f"Intentos: {result['attempts']}")
print(f"Respuesta final: {result['final_response']}")
```

### Ejemplo 3: Comparación

```python
# Consulta de comparación
query = "Compara las vacunas de Pfizer y Moderna"

# 1. Recuperar documentos para comparación
docs = retriever.retrieve_for_comparison(query, num_docs=6)

# 2. Generar comparación
response_data = rag_agent.generate_response(
    query=query,
    documents=docs,
    intent="comparacion"
)

# 3. Formatear con fuentes
formatted = rag_agent.format_response_with_sources(response_data)

print(formatted)

# 4. Validar
validation = critic.validate(query, response_data['response'], docs)

print(f"\nValidación:")
print(f"  Coherencia: {validation['criteria_scores']['coherence']}")
print(f"  Alineación: {validation['criteria_scores']['alignment']}")
print(f"  Alucinaciones: {validation['criteria_scores']['hallucination']}")
print(f"  Completitud: {validation['criteria_scores']['completeness']}")
print(f"  Citas: {validation['criteria_scores']['citation']}")
```

### Ejemplo 4: Integración con Orchestrator

```python
from src.agents.orchestrator import Orchestrator

# El orchestrator usa todos los agentes automáticamente
orchestrator = Orchestrator()

result = orchestrator.process_query(
    query="¿Qué es el COVID-19?",
    include_trace=True
)

print(f"Respuesta: {result['response']}")
print(f"Intención: {result['intent']}")
print(f"Estrategia: {result['strategy']}")
print(f"Documentos: {result['documents_found']}")
print(f"Regeneraciones: {result['regeneration_attempts']}")
print(f"Score validación: {result['validation']['overall_score']}")
```

---

## Conclusión

### Componentes Entregados

1. **RetrieverAgent** (`src/agents/retriever_agent.py`)
   - Optimización de queries con LLM
   - Consulta inteligente a FAISS
   - Métodos especializados por intención
   - Ranking y filtrado

2. **RAGAgent** (`src/agents/rag_agent.py`)
   - 3 prompts especializados
   - Generación con citas obligatorias
   - Respuestas generales sin RAG
   - Formateo de fuentes

3. **CriticAgent** (`src/agents/critic_agent.py`)
   - Evaluación 5 criterios
   - Detección de alucinaciones
   - Ciclo de regeneración
   - Score ponderado

4. **Documentación completa**
   - Prompts documentados
   - Proceso de verificación detallado
   - Ejemplos de uso
   - Métricas y evaluación

### Características Implementadas

- Recuperación semántica optimizada
- Generación RAG con prompts especializados
- Validación multi-criterio exhaustiva
- Ciclo de realimentación automático
- Sistema de citas [Fuente X]
- Detección de alucinaciones
- Logging y trazabilidad completa
- Manejo robusto de errores

### Integración con Sistema

Los 3 agentes se integran perfectamente con:
- **Orchestrator** (Persona 1): Coordina el flujo
- **ClassifierAgent** (Persona 1): Proporciona intención
- **VectorStoreManager** (Persona 2): Proporciona documentos
- **TraceManager**: Registra todas las operaciones

### Próximos Pasos (Persona 2)

Para completar el sistema, Persona 2 debe implementar:
- `VectorStoreManager` completo
- `EmbeddingsManager` completo
- Pipeline de indexación
- Loaders de documentos
- Herramientas de limpieza

Una vez implementado, el sistema estará completo y funcional.
