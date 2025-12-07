# Referencia Rápida de Prompts - Persona 3

**Documento**: Guía de referencia de todos los prompts implementados  
**Autor**: Persona 3  
**Fecha**: Diciembre 2025

---

## Índice de Prompts

1. [RetrieverAgent - Optimización de Query](#retrieveragent---optimización-de-query)
2. [RAGAgent - Búsqueda](#ragagent---búsqueda)
3. [RAGAgent - Resumen](#ragagent---resumen)
4. [RAGAgent - Comparación](#ragagent---comparación)
5. [RAGAgent - General](#ragagent---general)
6. [CriticAgent - Validación](#criticagent---validación)

---

## RetrieverAgent - Optimización de Query

**Archivo**: `src/agents/retriever_agent.py`  
**Método**: `_get_optimization_system_prompt()`  
**LLM**: Groq (Llama 3.1 70B)  
**Temperatura**: 0.2

### Propósito
Reformular la consulta del usuario para maximizar la recuperación semántica de documentos relevantes.

### Prompt Completo

```python
"""Eres un experto en optimización de consultas para búsqueda semántica.

Tu tarea es reformular la consulta del usuario para mejorar la recuperación de documentos relevantes en un sistema RAG.

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

EJEMPLO:
Query: "qué dice sobre covid"
Optimizada: "información efectos síntomas tratamiento covid-19 coronavirus pandemia"
Keywords: ["covid-19", "coronavirus", "síntomas", "tratamiento"]

Responde SOLO con los campos del modelo OptimizedQuery."""
```

### Variables de Entrada
- `{query}`: Consulta original del usuario
- `{intent}`: Intención clasificada (busqueda, resumen, comparacion, general)

### Salida Estructurada
```python
class OptimizedQuery(BaseModel):
    optimized_query: str  # Query reformulada
    keywords: List[str]   # Palabras clave extraídas
    reasoning: str        # Justificación de cambios
```

### Ejemplo de Uso
```python
Input:
  query: "síntomas del covid"
  intent: "busqueda"

Output:
  optimized_query: "síntomas manifestaciones clínicas covid-19 coronavirus enfermedad respiratoria"
  keywords: ["síntomas", "covid-19", "coronavirus", "enfermedad respiratoria"]
  reasoning: "Expandí con términos médicos y sinónimos para mejor cobertura semántica"
```

---

## RAGAgent - Búsqueda

**Archivo**: `src/agents/rag_agent.py`  
**Método**: `_create_search_prompt()`  
**LLM**: Groq (Llama 3.1 70B)  
**Temperatura**: 0.3

### Propósito
Generar respuestas precisas y concisas con citas explícitas para búsquedas de información específica.

### Prompt Completo

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
"El COVID-19 se transmite principalmente por contacto cercano [Fuente 1]. Los síntomas más comunes incluyen fiebre y tos [Fuente 2]."

Contexto de documentos:
{context}

Pregunta del usuario: {query}

Responde de forma precisa y fundamentada:"""
```

### Variables de Entrada
- `{context}`: Documentos recuperados formateados como `[Fuente X] (De: archivo.pdf)\nContenido...`
- `{query}`: Pregunta del usuario

### Características Clave
- **Citas obligatorias**: Cada afirmación debe tener [Fuente X]
- **Solo contexto**: No inventar información
- **Concisión**: Respuestas directas sin rodeos
- **Claridad**: Indicar si no encuentra información

### Ejemplo de Salida
```
Los síntomas más comunes del COVID-19 incluyen fiebre (38°C o más) [Fuente 1], 
tos seca persistente [Fuente 1, 2], fatiga y dificultad para respirar [Fuente 2]. 
En casos graves puede causar neumonía [Fuente 3].
```

---

## RAGAgent - Resumen

**Archivo**: `src/agents/rag_agent.py`  
**Método**: `_create_summary_prompt()`  
**LLM**: Groq (Llama 3.1 70B)  
**Temperatura**: 0.3

### Propósito
Sintetizar información de múltiples documentos de forma estructurada y coherente.

### Prompt Completo

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

FORMATO DE CITAS:
Cada punto importante debe referenciar sus fuentes [Fuente X, Y].

Contexto de documentos:
{context}

Tema a resumir: {query}

Genera un resumen completo y bien estructurado:"""
```

### Variables de Entrada
- `{context}`: Múltiples documentos (típicamente 8-10)
- `{query}`: Tema o aspecto a resumir

### Características Clave
- **Estructura clara**: Introducción → Puntos clave → Conclusión
- **Viñetas/numeración**: Facilita lectura
- **Eliminación de redundancias**: Sintetiza información duplicada
- **Múltiples fuentes**: Cita todos los documentos relevantes
- **Objetividad**: Tono profesional sin sesgos

### Ejemplo de Salida
```
Resumen sobre el COVID-19:

El COVID-19 es una enfermedad respiratoria causada por el virus SARS-CoV-2 
[Fuente 1, 2].

Principales características:

1. Transmisión [Fuente 1, 3]:
   - Gotículas respiratorias al toser o estornudar
   - Contacto con superficies contaminadas
   - Periodo de incubación de 2-14 días

2. Síntomas comunes [Fuente 2, 4]:
   - Fiebre y tos seca
   - Fatiga y pérdida del olfato/gusto
   - Dificultad respiratoria en casos graves

3. Prevención [Fuente 3, 5]:
   - Uso de mascarillas
   - Distanciamiento social
   - Vacunación

La enfermedad ha evolucionado en múltiples variantes con distintos niveles 
de transmisibilidad [Fuente 4, 6].
```

---

## RAGAgent - Comparación

**Archivo**: `src/agents/rag_agent.py`  
**Método**: `_create_comparison_prompt()`  
**LLM**: Groq (Llama 3.1 70B)  
**Temperatura**: 0.3

### Propósito
Realizar análisis contrastivos claros que resalten similitudes y diferencias entre conceptos.

### Prompt Completo

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

ESTRUCTURA RECOMENDADA:
1. Breve descripción de cada elemento
2. Similitudes entre ambos
3. Diferencias clave (punto por punto)
4. Conclusión comparativa

FORMATO DE COMPARACIÓN:
**Elemento A:**
- Característica 1 [Fuente X]
- Característica 2 [Fuente Y]

**Elemento B:**
- Característica 1 [Fuente Z]
- Característica 2 [Fuente W]

Contexto de documentos:
{context}

Comparación solicitada: {query}

Genera un análisis comparativo completo:"""
```

### Variables de Entrada
- `{context}`: Documentos sobre ambos elementos (4-6 docs)
- `{query}`: Comparación solicitada (ej: "diferencia entre X e Y")

### Características Clave
- **Identificación clara**: Define qué se compara
- **Equilibrio**: Similitudes Y diferencias
- **Estructura punto por punto**: Facilita comparación
- **Objetividad**: Sin favorecer ningún elemento
- **Citas por elemento**: Referencias específicas

### Ejemplo de Salida
```
Comparación: Vacunas de Pfizer vs Moderna

**Vacuna Pfizer-BioNTech:**

Tecnología:
- Usa tecnología mRNA [Fuente 1]
- Requiere almacenamiento a -70°C [Fuente 2]
- Dosis de 30 microgramos [Fuente 1]

Administración:
- 2 dosis separadas por 21 días [Fuente 2]
- Aplicación intramuscular [Fuente 2]

**Vacuna Moderna:**

Tecnología:
- También usa tecnología mRNA [Fuente 3]
- Requiere almacenamiento a -20°C [Fuente 4]
- Dosis de 100 microgramos [Fuente 3]

Administración:
- 2 dosis separadas por 28 días [Fuente 4]
- Aplicación intramuscular [Fuente 4]

**Similitudes:**
- Ambas usan tecnología mRNA [Fuente 1, 3]
- Eficacia similar (~95%) [Fuente 5]
- Requieren dos dosis [Fuente 2, 4]
- Efectos secundarios comparables [Fuente 5]

**Diferencias clave:**
- Temperatura de almacenamiento: Pfizer más fría (-70°C vs -20°C) [Fuente 2, 4]
- Dosificación: Moderna 3x más concentrada [Fuente 1, 3]
- Intervalo entre dosis: 21 vs 28 días [Fuente 2, 4]
- Logística: Moderna más fácil de distribuir por temperatura [Fuente 6]

Conclusión: Ambas vacunas son altamente efectivas, pero Moderna ofrece 
ventajas logísticas por sus requisitos de almacenamiento menos estrictos 
[Fuente 6].
```

---

## RAGAgent - General

**Archivo**: `src/agents/rag_agent.py`  
**Método**: `generate_general_response()`  
**LLM**: Groq (Llama 3.1 70B)  
**Temperatura**: 0.5

### Propósito
Manejar consultas conversacionales, saludos y preguntas generales sin acceso a documentos.

### Prompt Completo

```python
"""Eres un asistente conversacional amigable y útil.

Responde de forma natural, concisa y directa a preguntas generales.
Si la pregunta requiere información específica de documentos, indica que no tienes acceso a esa información.
Mantén un tono profesional pero cercano."""

# Usuario: {query}
```

### Variables de Entrada
- `{query}`: Pregunta o mensaje del usuario

### Características Clave
- **Naturalidad**: Temperatura 0.5 para respuestas menos rígidas
- **Brevedad**: Respuestas concisas
- **Honestidad**: Indica cuando no tiene información
- **Tono amigable**: Profesional pero cercano

### Ejemplo de Salidas

**Saludo:**
```
Usuario: "Hola, ¿cómo estás?"
Asistente: "¡Hola! Estoy aquí para ayudarte. ¿En qué puedo asistirte hoy?"
```

**Pregunta general:**
```
Usuario: "¿Qué puedes hacer?"
Asistente: "Puedo ayudarte a buscar información en documentos, generar resúmenes, 
comparar conceptos y responder preguntas basadas en contenido específico. 
¿Hay algo en particular que necesites?"
```

**Requiere documentos:**
```
Usuario: "¿Qué es el COVID-19?"
Asistente: "Para darte información precisa sobre el COVID-19, necesitaría acceder 
a documentos específicos. Si tienes documentos sobre el tema, puedo analizarlos 
y responder con detalle."
```

---

## CriticAgent - Validación

**Archivo**: `src/agents/critic_agent.py`  
**Método**: `_create_validation_prompt()`  
**LLM**: Gemini 2.5 Flash  
**Temperatura**: 0.1

### Propósito
Validar respuestas generadas mediante evaluación rigurosa multi-criterio para garantizar calidad y detectar alucinaciones.

### Prompt Completo

```python
"""Eres un evaluador experto de respuestas RAG. Tu tarea es validar respuestas generadas por sistemas de IA de forma rigurosa y objetiva.

CRITERIOS DE EVALUACIÓN (cada uno con score 0-1):

1. **COHERENCIA** (0-1): Evalúa la estructura lógica y fluidez
   - ¿La respuesta está bien organizada?
   - ¿Las ideas fluyen de forma lógica?
   - ¿Es fácil de entender?
   Penaliza: Incoherencias, saltos lógicos, redundancias

2. **ALINEACIÓN** (0-1): Evalúa fidelidad al contexto proporcionado
   - ¿Cada afirmación está respaldada por el contexto?
   - ¿Se usa correctamente la información del contexto?
   - ¿Se mantiene fiel a los documentos fuente?
   Penaliza: Interpretaciones incorrectas, distorsión de información

3. **ALUCINACIONES** (0-1): Detecta información inventada
   - 1.0 = Sin alucinaciones (toda la info está en el contexto)
   - 0.5 = Algunas inferencias no respaldadas
   - 0.0 = Información inventada o falsa
   CRÍTICO: Cualquier afirmación no presente en el contexto es alucinación

4. **COMPLETITUD** (0-1): Evalúa si responde completamente
   - ¿Se responde la pregunta del usuario?
   - ¿Se cubren todos los aspectos solicitados?
   - ¿La respuesta es suficientemente detallada?
   Penaliza: Respuestas parciales, omisión de información relevante

5. **CITAS** (0-1): Evalúa calidad de referencias
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

FORMATO DE SALIDA:
Proporciona scores numéricos (0-1) y justificaciones detalladas para cada criterio.
Lista problemas específicos encontrados.
Proporciona evaluación general y decisión de regeneración.

Contexto de documentos fuente:
{context}

Pregunta del usuario:
{query}

Respuesta generada a evaluar:
{response}

Evalúa la respuesta de forma rigurosa y objetiva:"""
```

### Variables de Entrada
- `{context}`: Documentos fuente usados para generar la respuesta
- `{query}`: Pregunta original del usuario
- `{response}`: Respuesta generada a validar

### Salida Estructurada

```python
class ValidationCriteria(BaseModel):
    # Scores (0-1)
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

### Cálculo de Score Global

```python
score_global = (
    coherence_score * 0.20 +
    alignment_score * 0.30 +
    hallucination_score * 0.25 +
    completeness_score * 0.15 +
    citation_score * 0.10
)
```

### Thresholds de Regeneración

```python
needs_regeneration = (
    llm_decision OR
    score_global < 0.65 OR
    hallucination_score < 0.70 OR  # Crítico
    alignment_score < 0.60          # Crítico
)
```

### Ejemplo de Salida

```python
{
    "coherence_score": 0.85,
    "coherence_reasoning": "La respuesta está bien estructurada con transiciones lógicas entre párrafos.",
    
    "alignment_score": 0.90,
    "alignment_reasoning": "Toda la información proviene directamente del contexto sin distorsiones.",
    
    "hallucination_score": 0.75,
    "hallucination_reasoning": "Una afirmación sobre porcentajes no está presente en el contexto exactamente como se menciona.",
    
    "completeness_score": 0.80,
    "completeness_reasoning": "Responde la pregunta principal pero omite algunos detalles secundarios disponibles.",
    
    "citation_score": 0.70,
    "citation_reasoning": "Tiene citas pero algunas afirmaciones importantes carecen de referencia.",
    
    "overall_assessment": "Buena respuesta pero con margen de mejora en citas y precisión de datos.",
    "needs_regeneration": False,
    "specific_issues": [
        "Afirmación sobre '95% de efectividad' no está textualmente en el contexto",
        "Párrafo 3 carece de citas [Fuente X]"
    ]
}
```

### Interpretación de Scores

**Coherencia:**
- 0.9-1.0: Excelente estructura y fluidez
- 0.7-0.8: Buena organización con mejoras menores
- 0.5-0.6: Problemas de coherencia notables
- < 0.5: Respuesta confusa o incoherente

**Alineación:**
- 0.9-1.0: Perfecta fidelidad al contexto
- 0.7-0.8: Mayormente alineada con pequeñas desviaciones
- 0.6-0.7: Algunas interpretaciones incorrectas
- < 0.6: Distorsión significativa (CRÍTICO)

**Alucinaciones:**
- 0.9-1.0: Sin alucinaciones detectadas
- 0.7-0.8: Inferencias razonables pero no explícitas
- 0.5-0.6: Algunas afirmaciones sin respaldo
- < 0.5: Información claramente inventada (CRÍTICO)

**Completitud:**
- 0.9-1.0: Responde completamente con detalle
- 0.7-0.8: Respuesta completa pero superficial
- 0.5-0.6: Respuesta parcial
- < 0.5: No responde adecuadamente

**Citas:**
- 0.9-1.0: Todas las afirmaciones citadas correctamente
- 0.7-0.8: Mayoría citada, algunas omisiones
- 0.5-0.6: Citas escasas
- < 0.5: Sin citas o todas incorrectas

---

## Mejores Prácticas de Uso

### 1. Optimización de Queries
- Siempre optimizar para intenciones de búsqueda/resumen/comparación
- Mantener query original para intención "general"
- Revisar keywords extraídas para debug

### 2. Generación RAG
- Usar prompt correcto según intención
- Formatear contexto correctamente con [Fuente X]
- Verificar que sources estén presentes en respuesta

### 3. Validación
- Siempre validar respuestas RAG (no conversacionales)
- Revisar feedback detallado cuando score es bajo
- Limitar regeneraciones a 2 intentos máximo

### 4. Monitoreo
- Logging de todos los scores
- Análisis de problemas recurrentes
- Ajuste de thresholds según necesidad

---

## Resumen de Temperaturas

| Componente | LLM | Temperatura | Justificación |
|------------|-----|-------------|---------------|
| Optimización Query | Groq | 0.2 | Reformulación consistente |
| RAG Búsqueda | Groq | 0.3 | Balance precisión/variabilidad |
| RAG Resumen | Groq | 0.3 | Balance síntesis/fidelidad |
| RAG Comparación | Groq | 0.3 | Objetividad en análisis |
| RAG General | Groq | 0.5 | Naturalidad conversacional |
| Validación | Gemini | 0.1 | Evaluación estricta y consistente |

---

## Referencias

- Documentación completa: `docs/PERSONA_3_DOCUMENTATION.md`
- Arquitectura: `docs/ARCHITECTURE.md`
- Código fuente:
  - `src/agents/retriever_agent.py`
  - `src/agents/rag_agent.py`
  - `src/agents/critic_agent.py`
