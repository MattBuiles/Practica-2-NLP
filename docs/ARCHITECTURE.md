# Arquitectura del Sistema Agentic AI

## Visión General

El sistema implementa una arquitectura multi-agente basada en LangChain 1.0 para procesamiento de documentos mediante RAG (Retrieval-Augmented Generation).

## Componentes Principales

### 1. Orquestador (`orchestrator.py`)

**Responsabilidad**: Coordinación central del flujo de ejecución

**Decisiones clave**:
- Routing de consultas según intención
- Gestión de trazabilidad
- Manejo de errores y fallbacks
- Coordinación entre agentes

**Flujo**:
```
Query → Classify → Route → Retrieve → Generate → Validate → Response
```

### 2. Agente Clasificador (`classifier_agent.py`)

**LLM**: Gemini 2.5 Flash

**Justificación**: Superior comprensión contextual para análisis semántico profundo

**Responsabilidades**:
- Clasificar intención en 4 categorías:
  - `busqueda`: Información específica del corpus
  - `resumen`: Resumen de documentos
  - `comparacion`: Comparar documentos/conceptos
  - `general`: Sin necesidad de RAG
- Determinar si requiere acceso al vector store
- Proporcionar razonamiento de la decisión

**Temperatura**: 0.1 (clasificación consistente)

### 3. Agente Recuperador (`retriever_agent.py`) - IMPLEMENTADO (Persona 3)

**Estado**: Completamente implementado

**LLM**: Groq (Llama 3.1 70B)

**Justificación**: Latencia mínima para optimización rápida de consultas

**Responsabilidades**:
- Optimizar consultas para mejor recuperación usando LLM
- Búsqueda semántica en FAISS (asume vectorstore implementado)
- Rankear y filtrar resultados por score threshold
- Adaptar recuperación según intención

**Temperatura**: 0.2

**Métodos implementados**:
- `retrieve()`: Recuperación estándar con optimización opcional
- `retrieve_for_comparison()`: Recupera 4-6 docs con threshold bajo (0.3)
- `retrieve_for_summary()`: Recupera 8-10 docs con threshold moderado (0.4)
- `_optimize_query()`: Reformula query con LLM para mejor recuperación
- `_rank_and_filter()`: Filtra por score y ordena por relevancia

**Optimización de queries**:
- Expande con sinónimos y términos relacionados
- Elimina ambigüedades
- Extrae keywords principales
- Adapta estrategia según intención

**Documentación**: Ver `docs/PERSONA_3_DOCUMENTATION.md`

### 4. Agente RAG (`rag_agent.py`) - IMPLEMENTADO (Persona 3)

**Estado**: Completamente implementado

**LLM**: Groq (Llama 3.1 70B)

**Justificación**: Velocidad de generación con baja latencia

**Responsabilidades**:
- Generar respuestas basadas en contexto recuperado
- Incluir citas obligatorias [Fuente X]
- Adaptar estilo según intención
- Respuestas generales sin RAG para consultas conversacionales

**Temperatura**: 0.3 (RAG), 0.5 (General)

**Prompts especializados implementados**:

1. **Búsqueda**: 
   - Respuestas precisas y concisas
   - Citas explícitas para cada afirmación
   - Instrucciones para no inventar información
   - Formato: "Afirmación [Fuente X]"

2. **Resumen**: 
   - Síntesis estructurada con viñetas
   - Identificación de puntos clave
   - Eliminación de redundancias
   - Estructura: Intro → Puntos clave → Conclusión

3. **Comparación**: 
   - Análisis contrastivo punto por punto
   - Similitudes Y diferencias
   - Formato estructurado
   - Evaluación objetiva sin sesgos

**Métodos implementados**:
- `generate_response()`: Generación con contexto (selecciona prompt según intent)
- `generate_general_response()`: Respuestas sin RAG
- `format_response_with_sources()`: Añade sección de fuentes
- `_format_context()`: Formatea documentos para LLM
- `_extract_sources()`: Extrae metadata de fuentes

**Documentación completa de prompts**: Ver `docs/PERSONA_3_DOCUMENTATION.md`

### 5. Agente Crítico (`critic_agent.py`) - IMPLEMENTADO (Persona 3)

**Estado**: Completamente implementado con ciclo de regeneración

**LLM**: Gemini 2.5 Flash

**Justificación**: Razonamiento profundo para validación compleja

**Responsabilidades**:
- Validar coherencia estructural
- Detectar alucinaciones (información inventada)
- Verificar alineación con contexto fuente
- Evaluar completitud y calidad de citas
- Decidir regeneración automática (máx 2 intentos)

**Temperatura**: 0.1 (evaluación estricta)

**Sistema de validación multi-criterio**:

1. **Coherencia (20%)**:
   - Estructura lógica y fluidez
   - Transiciones entre ideas
   - Facilidad de comprensión

2. **Alineación (30%)** - Peso más alto:
   - Fidelidad al contexto proporcionado
   - Uso correcto de información fuente
   - Interpretaciones precisas
   - Threshold crítico: 0.60

3. **Alucinaciones (25%)** - Crítico:
   - Ausencia de información inventada
   - Todas las afirmaciones respaldadas
   - Score alto = sin alucinaciones
   - Threshold crítico: 0.70

4. **Completitud (15%)**:
   - Responde completamente la pregunta
   - Cubre aspectos solicitados
   - Nivel de detalle adecuado

5. **Citas (10%)**:
   - Presencia de [Fuente X]
   - Calidad de referencias
   - Cobertura de afirmaciones

**Score global ponderado**:
```
score = coherence*0.20 + alignment*0.30 + hallucination*0.25 + 
        completeness*0.15 + citation*0.10
```

**Thresholds de decisión**:
- Score mínimo global: 0.65
- Alucinaciones mínimo: 0.70 (crítico)
- Alineación mínimo: 0.60 (crítico)

**Ciclo de regeneración**:
- Método `validate_with_regeneration()` implementado
- Máximo 2 intentos de generación
- Regeneración automática si score insuficiente
- Selección de mejor respuesta si se alcanza máximo
- Historial completo de todos los intentos

**Documentación completa**: Ver `docs/PERSONA_3_DOCUMENTATION.md`

### 6. Agente Indexador (`indexer_agent.py`)

**Responsabilidades**:
- Carga de documentos (PDF, HTML, TXT)
- Limpieza y normalización
- Chunking inteligente
- Indexación en FAISS

**Pipeline**:
```
Documentos → Limpiar → Chunkear → Embeddear → Indexar FAISS
```

## Pipeline RAG

### Embeddings (`embeddings.py`)

**Modelo**: `sentence-transformers/all-MiniLM-L6-v2`

**Características**:
- Dimensión: 384
- Normalización: Sí
- Device: CPU (configurable a GPU)

### Chunking (`chunking.py`)

**Estrategia**: RecursiveCharacterTextSplitter

**Parámetros**:
- Chunk size: 1000 caracteres
- Overlap: 200 caracteres
- Separadores: `["\n\n", "\n", ". ", " ", ""]`

**Metadata por chunk**:
- Índice de chunk
- Total de chunks del documento
- Documento original
- Fuente

### Vector Store (`vectorstore.py`)

**Tecnología**: FAISS

**Tipo de índice**: L2 (Euclidean distance)

**Funcionalidades**:
- Creación de índice
- Adición de documentos
- Búsqueda por similitud
- Persistencia en disco
- Carga de índice existente

## Sistema de Trazabilidad

### ExecutionTrace (`tracing.py`)

**Información registrada**:
- Session ID único
- Query original
- Tiempo de ejecución
- Pasos ejecutados
- Agentes involucrados
- Llamadas LLM
- Documentos recuperados
- Regeneraciones

**Persistencia**:
- JSON para procesamiento
- Markdown para lectura humana

### Métodos de registro**:
- `add_classification()`: Resultado del clasificador
- `add_retrieval()`: Documentos recuperados
- `add_generation()`: Respuesta generada
- `add_validation()`: Resultado del crítico

## Evaluación de Calidad

### ResponseEvaluator (`evaluators.py`)

**Métricas automáticas**:

1. **Coherencia**:
   - Longitud adecuada
   - Estructura correcta
   - Completitud de frases

2. **Alineación con contexto**:
   - Overlap de términos
   - Uso de información del contexto

3. **Detección de alucinaciones**:
   - Afirmaciones categóricas sin soporte
   - Estadísticas no presentes en contexto
   - Indicadores de invención

4. **Completitud**:
   - Cobertura de la consulta
   - Estructura apropiada (resumen/comparación)

5. **Citas**:
   - Presencia de referencias
   - Formato correcto

**Score general**: Promedio ponderado de todas las métricas

## Herramientas (Tools)

### PDFLoaderTool
- Carga PDFs con PyPDF
- Extrae texto por página
- Metadata de fuente

### HTMLLoaderTool
- Parseo con BeautifulSoup
- Limpieza de scripts/estilos
- Extracción de título

### TextCleanerTool
- Normalización de espacios
- Remoción de caracteres de control
- Limpieza agresiva (opcional)
- Filtrado por longitud

### TraceExporterTool
- Exportación de casos de uso
- Formato JSON y Markdown
- Batch export

## Configuración

### LLM Config (`llm_config.py`)

**Gemini**:
- Modelo: gemini-1.5-flash
- Usos: Clasificador, Crítico
- Temperatura: 0.1

**Groq**:
- Modelo: llama-3.1-70b-versatile
- Usos: Recuperador, RAG, Orquestador
- Temperatura: 0.1-0.5 según agente

### Settings (`settings.yaml`)

Configuración de:
- Embeddings
- FAISS
- Agentes
- Trazabilidad
- Dominio
- Procesamiento

## Flujo de Ejecución Completo

```
┌─────────────────────────────────────────────────┐
│              Usuario: Query                      │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│         Orchestrator: Iniciar Traza             │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│  Classifier (Gemini): Clasificar Intención      │
│  → busqueda / resumen / comparacion / general   │
└─────────────────┬───────────────────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
    requires_rag?          │
         │                 │
      NO │              SÍ │
         │                 │
         ▼                 ▼
┌──────────────┐  ┌────────────────────────────┐
│   Respuesta  │  │  Retriever (Groq):         │
│   General    │  │  Optimizar + Buscar FAISS  │
│   (Groq)     │  └────────┬───────────────────┘
└──────────────┘           │
                           ▼
                  ┌────────────────────────────┐
                  │  RAG Agent (Groq):         │
                  │  Generar con Contexto      │
                  └────────┬───────────────────┘
                           │
                           ▼
                  ┌────────────────────────────┐
                  │  Critic (Gemini):          │
                  │  Validar Respuesta         │
                  └────────┬───────────────────┘
                           │
                    ┌──────┴──────┐
                    │             │
                 válida?          │
                    │             │
                 SÍ │          NO │
                    │             │
                    │             ▼
                    │   ┌──────────────────┐
                    │   │  Regenerar       │
                    │   │  (máx 2 veces)   │
                    │   └─────────┬────────┘
                    │             │
                    └─────────────┘
                           │
                           ▼
                  ┌────────────────────────────┐
                  │  Finalizar Traza           │
                  │  Formatear Respuesta       │
                  └────────┬───────────────────┘
                           │
                           ▼
                  ┌────────────────────────────┐
                  │  Respuesta Final + Fuentes │
                  └────────────────────────────┘
```

## Ventajas de la Arquitectura

1. **Modularidad**: Cada agente es independiente y reutilizable
2. **Especialización**: LLMs optimizados por tarea
3. **Trazabilidad**: Registro completo de decisiones
4. **Validación**: Calidad garantizada por agente crítico
5. **Escalabilidad**: Fácil añadir nuevos agentes
6. **Flexibilidad**: Configuración centralizada

## Limitaciones y Mejoras Futuras

**Limitaciones actuales**:
- Procesamiento secuencial (no paralelo)
- Validación limitada a 2 regeneraciones
- Sin caché de respuestas
- Sin fine-tuning de embeddings

**Mejoras propuestas**:
- Procesamiento paralelo de chunks
- MMR para diversidad en recuperación
- Caché inteligente de respuestas
- Re-ranking con modelo cross-encoder
- Fine-tuning de embeddings por dominio
- Agente de memoria conversacional
