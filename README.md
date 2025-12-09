# Sistema Agentic AI - Práctica 3 NLP

## 📋 División de Responsabilidades del Equipo

### ✅ Persona 1: Arquitectura, Orquestador y Clasificador (IMPLEMENTADO)

**Componentes Completados:**
- ✅ Arquitectura completa del sistema
- ✅ Agente Orquestador
- ✅ Agente Clasificador (Gemini)
- ✅ Sistema de Trazabilidad
- ✅ Configuración LLM con justificación

### ✅ Persona 3: Recuperación, Generación y Validación (IMPLEMENTADO)

**Componentes Completados:**
- ✅ RetrieverAgent (Optimización + FAISS)
- ✅ RAGAgent (Prompts especializados + Generación)
- ✅ CriticAgent (Validación multi-criterio + Regeneración)
- ✅ Ciclo de realimentación completo
- ✅ Documentación técnica exhaustiva

### ✅ Persona 2: Ingestión y Vector Store (IMPLEMENTADO)

**Componentes Completados:**
- ✅ VectorStoreManager (FAISS) - Búsqueda semántica eficiente
- ✅ EmbeddingsManager - Generación de embeddings con sentence-transformers
- ✅ RAG Pipeline - Orquestación completa de indexación y búsqueda
- ✅ Tools - Loaders (PDF, HTML, TXT) y TextCleaner
- ✅ DocumentChunker - Chunking inteligente con overlap
- ✅ IndexerAgent - Pipeline completo de indexación

## 🎯 Funcionalidad Actual (Persona 1)

- **Clasificación de Intención**: 4 tipos (búsqueda, resumen, comparación, general)
- **Orquestación**: Coordinación del flujo entre agentes
- **Trazabilidad Completa**: Registro de todas las decisiones
- **Uso Diferenciado de LLMs**: Gemini (clasificación) y Groq (coordinación)

## 📋 Requisitos

- Python 3.9+
- API Keys:
  - Google AI (Gemini)
  - Groq

## 🚀 Instalación

1. Clonar repositorio:
```bash
git clone <repository-url>
cd Practica-2-NLP
```

2. Crear entorno virtual:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
Crear archivo `.env` en la raíz:
```env
GOOGLE_API_KEY=tu_api_key_de_google
GROQ_API_KEY=tu_api_key_de_groq
```

## 🏗️ Arquitectura del Sistema

```
Usuario
   ↓
[Orchestrator] ✅ IMPLEMENTADO (Persona 1)
   ↓
┌──────────────────────┐
│ 1. Clasificador      │ ✅ IMPLEMENTADO (Persona 1)
│    - Gemini 1.5      │
│    - 4 intenciones   │
└──────────────────────┘
   ↓
┌──────────────────────┐
│ 2. Retriever         │ ✅ IMPLEMENTADO (Persona 3)
│    - Groq Llama      │
│    - FAISS Search    │
│    - Optimización    │
└──────────────────────┘
   ↓
┌──────────────────────┐
│ 3. RAG Agent         │ ✅ IMPLEMENTADO (Persona 3)
│    - Groq Llama      │
│    - Generación      │
│    - Prompts         │
└──────────────────────┘
   ↓
┌──────────────────────┐
│ 4. Critic Agent      │ ✅ IMPLEMENTADO (Persona 3)
│    - Gemini 2.5      │
│    - Validación      │
│    - Regeneración    │
└──────────────────────┘
   ↓
Respuesta Final
```

### Flujo Implementado:

1. **Usuario** → Orchestrator
2. **Clasificador (Gemini)** → Determina intención
3. **Orchestrator** → Routing según intención
4. **Trazabilidad** → Registra cada paso

**Nota:** Todos los componentes están implementados. Persona 2 maneja la indexación y Persona 3 maneja la recuperación, generación y validación.

```
Practica-2-NLP/
├── src/
│   ├── agents/              # Agentes especializados
│   │   ├── classifier_agent.py
│   │   ├── retriever_agent.py
│   │   ├── rag_agent.py
│   │   ├── critic_agent.py
│   │   ├── indexer_agent.py
│   │   └── orchestrator.py
│   ├── config/              # Configuración
│   ├── rag_pipeline/        # Pipeline RAG
│   ├── tools/               # Herramientas
│   └── utils/               # Utilidades
├── data/
│   ├── raw/                 # Documentos originales (mín. 100)
│   ├── processed/
│   └── vectorstore/         # Índice FAISS
├── logs/                    # Logs del sistema
├── results/                 # Resultados y casos de uso
├── main.py                  # Punto de entrada
└── requirements.txt
```

## 💻 Uso

### 1. Indexar Documentos

Coloca tus documentos (PDF, HTML, TXT) en `data/raw/` y ejecuta:

```bash
python main.py --index
```

### 2. Modo Interactivo

```bash
python main.py --interactive
```

o simplemente:

```bash
python main.py
```

### 3. Modo Batch

Crea un archivo con consultas (una por línea):

```bash
python main.py --batch queries.txt
```

## 🤖 Agentes del Sistema

### 1. Clasificador de Intención (Gemini)
- Clasifica consultas en 4 categorías
- Determina si requiere RAG
- Proporciona razonamiento

### 2. Recuperador Semántico (Groq)
- Optimiza consultas
- Búsqueda en FAISS
- Rankea resultados

### 3. Generador RAG (Groq)
- Genera respuestas con contexto
- Incluye citas
- Adapta según intención

### 4. Crítico/Verificador (Gemini)
- Valida coherencia
- Detecta alucinaciones
- Regenera si es necesario

### 5. Indexador (Persona 2)
- Carga documentos (PDF, HTML, TXT)
- Limpieza y normalización de texto
- Chunking inteligente con overlap
- Generación de embeddings
- Indexación en FAISS
- Persistencia de índices

## 📊 Ejemplos de Uso

```python
from src.agents.orchestrator import Orchestrator

# Inicializar sistema
orchestrator = Orchestrator()

# Procesar consulta
result = orchestrator.process_query("¿Qué es la diabetes?")

print(result['response'])
print(result['sources'])
```

## 🔧 Configuración

Edita `src/config/settings.yaml` para ajustar:

- Tamaño de chunks
- Número de documentos a recuperar
- Criterios de validación
- Y más...

## 📈 Casos de Uso

Los casos de uso se exportan automáticamente a:
- JSON: `results/casos_de_uso/caso_XX.json`
- Markdown: `results/casos_de_uso/caso_XX.md`

## 🎓 Arquitectura

```
Usuario → Orquestador → Clasificador (Gemini)
                    ↓
        ¿Requiere RAG? → NO → Respuesta General
                    ↓ SÍ
            Recuperador (Groq) → FAISS
                    ↓
            Generador RAG (Groq)
                    ↓
            Crítico (Gemini) → ¿Válida?
                    ↓ NO → Regenerar (máx 2 intentos)
                    ↓ SÍ
                Respuesta Final
```

## 📝 Justificación de LLMs

### Gemini (Google AI)
- **Clasificador**: Mejor comprensión contextual profunda
- **Crítico**: Razonamiento complejo para validación

### Groq
- **Recuperador**: Latencia mínima para optimización
- **RAG**: Velocidad en generación de respuestas

## 🐛 Troubleshooting

### Error: No se encuentra el índice
```bash
python main.py --index
```

### Error: API Keys
Verifica que `.env` contenga las claves correctas.

### Error: Dependencias
```bash
pip install -r requirements.txt --upgrade
```

## 👥 Autores

Práctica 3 - Procesamiento de Lenguaje Natural
- Persona 1: Arquitectura, Orquestador y Clasificador
- Persona 2: Ingestión, Limpieza, Embeddings y Vector Store
- Persona 3: Recuperación, Generación y Validación

## 📄 Licencia

MIT License

## 🔗 Referencias

- [LangChain Documentation](https://python.langchain.com/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [Sentence Transformers](https://www.sbert.net/)