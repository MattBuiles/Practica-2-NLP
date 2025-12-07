# Demo: Persona 1 + Persona 3

Este script demuestra la funcionalidad completa de los componentes implementados por Persona 1 y Persona 3.

## Requisitos

```bash
pip install -r requirements.txt
```

Necesitas configurar las API keys en un archivo `.env`:

```env
GOOGLE_API_KEY=tu_google_api_key
GROQ_API_KEY=tu_groq_api_key
```

## Ejecutar la demo

```bash
python demo_persona_1_3.py
```

## Qué hace la demo

La demo ejecuta **6 pruebas** que muestran todos los componentes funcionando:

### Prueba 1: ClassifierAgent (Persona 1)
- Clasifica la intención de una consulta
- Determina si requiere RAG o no
- Proporciona razonamiento de la decisión

### Prueba 2: RetrieverAgent (Persona 3)
- Optimiza la query con LLM
- Recupera documentos relevantes del vector store
- Rankea y filtra por score de similitud

### Prueba 3: RAGAgent (Persona 3)
- Selecciona prompt especializado según intención
- Genera respuesta basada en documentos
- Incluye citas [Fuente X]
- Extrae fuentes utilizadas

### Prueba 4: CriticAgent (Persona 3)
- Valida respuesta con 5 criterios:
  - Coherencia (20%)
  - Alineación (30%)
  - Alucinaciones (25%)
  - Completitud (15%)
  - Citas (10%)
- Calcula score global ponderado
- Decide si regenerar

### Prueba 5: Ciclo de Regeneración (Persona 3)
- Valida respuesta inicial
- Regenera automáticamente si score insuficiente
- Máximo 2 intentos
- Selecciona mejor respuesta

### Prueba 6: Orchestrator - Flujo Completo (Persona 1)
- **Caso 1**: Query de búsqueda con RAG completo
- **Caso 2**: Query general sin RAG
- Muestra todo el flujo: Clasificar → Decidir → Recuperar → Generar → Validar

## Datos Mock

La demo usa un **MockVectorStoreManager** que simula FAISS con 5 documentos sobre COVID-19:

- Información general sobre COVID-19
- Síntomas comunes
- Medidas de prevención
- Vacunas
- Tratamiento

Esto permite probar toda la funcionalidad sin necesitar el vector store real que implementará Persona 2.

## Salida esperada

La demo mostrará:

```
================================================================================
DEMO: Sistema Agentic AI - Persona 1 + Persona 3
================================================================================

[MOCK] VectorStoreManager inicializado con documentos mock de COVID-19

================================================================================
Importando componentes implementados...
================================================================================
✓ ClassifierAgent (Persona 1) importado
✓ Orchestrator (Persona 1) importado
✓ RetrieverAgent (Persona 3) importado
✓ RAGAgent (Persona 3) importado
✓ CriticAgent (Persona 3) importado

================================================================================
PRUEBA 1: ClassifierAgent (Persona 1)
================================================================================
...
```

## Componentes probados

### Persona 1 (Completamente funcional):
- ✅ ClassifierAgent
- ✅ Orchestrator

### Persona 3 (Completamente funcional):
- ✅ RetrieverAgent
- ✅ RAGAgent
- ✅ CriticAgent
- ✅ Ciclo de regeneración

## Próximos pasos

1. **Persona 2**: Reemplazar MockVectorStoreManager con FAISS real
2. **Persona 2**: Indexar 100 documentos del dominio
3. **Persona 4**: Crear interfaz de usuario
4. **Persona 4**: Diseñar 10 casos de uso completos

## Notas técnicas

- Los LLMs usados son reales (Gemini y Groq)
- Solo el vector store es mock
- Todas las respuestas son generadas por los LLMs reales
- La validación usa Gemini 2.5 Flash real
- Los prompts especializados están completamente implementados

## Troubleshooting

**Error: ModuleNotFoundError**
```bash
pip install -r requirements.txt
```

**Error: API Key not found**
```bash
# Crea archivo .env con tus API keys
GOOGLE_API_KEY=...
GROQ_API_KEY=...
```

**Error: Rate limit**
- Espera unos segundos entre ejecuciones
- Verifica tus límites de API en Groq y Google AI

## Estructura de pruebas

```
demo_persona_1_3.py
├── MockVectorStoreManager (simula Persona 2)
├── Prueba 1: Clasificación
├── Prueba 2: Recuperación
├── Prueba 3: Generación RAG
├── Prueba 4: Validación
├── Prueba 5: Ciclo regeneración
└── Prueba 6: Flujo completo
```

## Tiempo de ejecución

Aproximadamente **30-60 segundos** dependiendo de:
- Latencia de APIs (Groq y Gemini)
- Número de regeneraciones necesarias
- Velocidad de conexión

## Logs generados

La demo genera logs detallados de:
- Cada paso del proceso
- Decisiones del orquestador
- Scores de validación
- Documentos recuperados
- Prompts utilizados

Útil para debugging y comprensión del flujo.
