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

### 3. Agente Recuperador (`retriever_agent.py`)

**LLM**: Groq (Llama 3.1 70B)

**Justificación**: Latencia mínima para optimización rápida de consultas

**Responsabilidades**:
- Optimizar consultas para mejor recuperación
- Búsqueda semántica en FAISS
- Rankear y filtrar resultados
- Adaptar recuperación según intención

**Temperatura**: 0.2

**Métodos especializados**:
- `retrieve_for_comparison()`: Para comparaciones
- `retrieve_for_summary()`: Para resúmenes

### 4. Agente RAG (`rag_agent.py`)

**LLM**: Groq (Llama 3.1 70B)

**Justificación**: Velocidad de generación con baja latencia

**Responsabilidades**:
- Generar respuestas basadas en contexto
- Incluir citas de fuentes
- Adaptar estilo según intención
- Respuestas generales (sin RAG)

**Temperatura**: 0.3 (balance creatividad/precisión)

**Prompts especializados**:
- Búsqueda: Respuestas precisas con citas
- Resumen: Extracción de puntos clave
- Comparación: Análisis contrastivo

### 5. Agente Crítico (`critic_agent.py`)

**LLM**: Gemini 2.5 Flash

**Justificación**: Razonamiento profundo para validación compleja

**Responsabilidades**:
- Validar coherencia
- Detectar alucinaciones
- Verificar alineación con contexto
- Decidir regeneración (máx 2 intentos)

**Temperatura**: 0.1 (evaluación estricta)

**Criterios de validación**:
1. Coherencia estructural
2. Alineación con contexto
3. Ausencia de alucinaciones
4. Completitud de respuesta
5. Calidad de citas

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
