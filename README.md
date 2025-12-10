# Sistema RAG Autónomo - Dinosaurios

Sistema de Generación Aumentada por Recuperación (RAG) con agentes autónomos especializados para responder preguntas sobre dinosaurios usando un corpus de 100+ documentos científicos.

## 🎯 Características Principales

- ✅ **Sistema RAG Completo**: Clasificación, recuperación, generación y validación
- ✅ **Agentes Autónomos**: 4 agentes especializados con LangChain 1.1
- ✅ **Vector Store**: FAISS con 6054 documentos indexados
- ✅ **LLM Groq**: Llama-3.3-70b-versatile para todos los agentes
- ✅ **Validación Automática**: Critic agent con regeneración si es necesario
- ✅ **Trazabilidad Completa**: Logs detallados y exportación de resultados
- ✅ **UI Streamlit**: Interfaz web para pruebas interactivas
- ✅ **Testing Automatizado**: Suite de tests con 10 casos de uso

## 📋 Requisitos

- Python 3.9+
- API Keys:
  - Groq API (para LLM Llama-3.3-70b-versatile)

## 🚀 Instalación

1. **Clonar repositorio:**
```bash
git clone <repository-url>
cd Practica-2-NLP
```

2. **Crear entorno virtual:**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno:**
Crear archivo `.env` en la raíz:
```env
GROQ_API_KEY=tu_api_key_de_groq
```

## 🏗️ Arquitectura del Sistema

### Flujo de Procesamiento

```
Usuario
   ↓
[AutonomousOrchestrator]
   ↓
┌─────────────────────────────┐
│ 1. ClassifierAgent (Groq)  │
│    - Clasifica intención    │
│    - Determina si usa RAG   │
└─────────────────────────────┘
   ↓
┌─────────────────────────────┐
│ 2. RetrieverAgent (Groq)   │
│    - Optimiza query         │
│    - Búsqueda en FAISS      │
│    - Retorna docs relevantes│
└─────────────────────────────┘
   ↓
┌─────────────────────────────┐
│ 3. RAGAgent (Groq)         │
│    - Genera respuesta       │
│    - Incluye fuentes        │
│    - Adapta por intención   │
└─────────────────────────────┘
   ↓
┌─────────────────────────────┐
│ 4. CriticAgent (Groq)      │
│    - Valida calidad         │
│    - Detecta alucinaciones  │
│    - Regenera si necesario  │
└─────────────────────────────┘
   ↓
Respuesta Final + Metadatos

```

### Estructura del Proyecto

```
Practica-2-NLP/
├── src/
│   ├── agents/                    # Agentes autónomos
│   │   ├── autonomous_classifier_agent.py
│   │   ├── autonomous_retriever_agent.py
│   │   ├── autonomous_rag_agent.py
│   │   ├── autonomous_critic_agent.py
│   │   └── autonomous_orchestrator.py
│   ├── config/                    # Configuración LLM
│   │   └── llm_config.py
│   ├── rag_pipeline/              # Pipeline RAG
│   │   ├── embeddings_manager.py
│   │   ├── vectorstore_manager.py
│   │   └── document_chunker.py
│   ├── tools/                     # Herramientas LangChain
│   │   ├── document_search_tool.py
│   │   ├── response_generator_tool.py
│   │   ├── validation_tool.py
│   │   └── logging_tool.py
│   └── utils/                     # Utilidades
├── data/
│   ├── raw/                       # 100+ docs sobre dinosaurios
│   └── vectorstore/
│       └── faiss_index/           # Índice FAISS (6054 chunks)
├── logs/                          # Trazas del sistema
├── results/
│   ├── casos_de_uso/              # Resultados individuales
│   └── respuestas/                # Batches de resultados
├── docs/                          # Documentación técnica
├── main.py                        # Punto de entrada principal
├── ui_dinosaurios.py              # UI Streamlit
├── test_dinosaurios.py            # Suite de tests
└── requirements.txt
```

## 💻 Uso del Sistema

### 1. Indexación de Documentos

**Nota**: El vector store ya está indexado con 6054 documentos sobre dinosaurios.

Si necesitas reindexar:

```bash
python main.py --index
```

### 2. Interfaz Web (Streamlit)

```bash
streamlit run ui_dinosaurios.py
```

Accede a `http://localhost:8501` y prueba los 10 casos de uso predefinidos.

### 3. Tests Automatizados

**Modo completo** (10 casos de uso):
```bash
python test_dinosaurios.py
```

**Modo debug** (2 casos):
```bash
python test_dinosaurios.py --debug
```

Los resultados se exportan a:
- `results/casos_de_uso/` - Archivos JSON individuales
- `results/respuestas/` - Batches completos
- `logs/` - Logs detallados

### 4. Uso Programático

```python
from src.agents.autonomous_orchestrator import AutonomousOrchestrator

# Inicializar
orchestrator = AutonomousOrchestrator()

# Procesar consulta
result = orchestrator.process_query(
    "¿Cuáles fueron los dinosaurios más grandes?"
)

# Resultados
print(f"Respuesta: {result['response']}")
print(f"Intención: {result['intent']}")
print(f"Estrategia: {result['strategy']}")
print(f"Documentos: {result['num_documents']}")
print(f"Validación: {result['validation_score']}")
```

## 🤖 Agentes del Sistema

### 1. ClassifierAgent (Groq)
**Propósito**: Clasificar la intención del usuario

**Intenciones**:
- `busqueda`: Búsqueda de información específica
- `resumen`: Solicitud de resumen
- `comparacion`: Comparación de conceptos
- `general`: Conversación general (no requiere RAG)

**Output**:
```json
{
  "intent": "busqueda",
  "confidence": 0.9,
  "requires_rag": true,
  "reasoning": "Usuario busca información específica sobre T-Rex"
}
```

### 2. RetrieverAgent (Groq)
**Propósito**: Recuperar documentos relevantes del vector store

**Capacidades**:
- Optimización de query con LLM
- Búsqueda semántica en FAISS
- Filtrado por metadata
- Ranking de resultados

**Output**: Lista de documentos con metadata y scores

### 3. RAGAgent (Groq)
**Propósito**: Generar respuesta usando contexto recuperado

**Características**:
- Prompts especializados por intención
- Inclusión de fuentes con nombres de documentos
- Sección de referencias
- Adaptación según tipo de consulta

**Output**: Respuesta + referencias formateadas

### 4. CriticAgent (Groq)
**Propósito**: Validar calidad de la respuesta

**Criterios de validación**:
- Coherencia con documentos
- Detección de alucinaciones
- Completitud de la información
- Calidad de las fuentes

**Output**:
```json
{
  "is_valid": true,
  "score": 0.9,
  "should_regenerate": false,
  "feedback": "Respuesta coherente y bien fundamentada"
}
```

**Regeneración**: Hasta 2 intentos si la validación falla

## 📊 Casos de Uso

El sistema incluye 10 casos de uso sobre dinosaurios:

1. **Información General**: Dinosaurios más grandes
2. **Anatomía**: Brazos del T-Rex
3. **Comportamiento**: Dinosaurios buenos padres
4. **Descubrimientos**: Procedimiento al encontrar fósiles
5. **Extinción**: Cómo se extinguieron
6. **Alimentación**: Qué comían
7. **Hábitat**: Dónde vivían
8. **Comparación**: Carnívoros vs Herbívoros
9. **Resumen**: Titanosaurios
10. **Conversacional**: Saludo

### Ejemplo de Output

```json
{
  "query": "¿Cuáles fueron los dinosaurios más grandes?",
  "intent": "busqueda",
  "strategy": "simple_rag",
  "documents_retrieved": 5,
  "response": "Los dinosaurios más grandes fueron los titanosaurios...",
  "validation_score": 0.9,
  "processing_time": 10.5,
  "sources": [
    "Why were dinosaurs so big.html",
    "Preparación de fósiles.html"
  ]
}
```

## 🔧 Configuración Técnica

### LLM Configuration

**Todos los agentes usan Groq**:
- Modelo: `llama-3.3-70b-versatile`
- Temperatura: 0.3 (respuestas consistentes)
- Max tokens: 2000
- API Delay: 1.5s (evitar rate limiting)

**Por qué Groq**:
- ✅ Velocidad: Latencia ultra-baja
- ✅ Consistencia: Respuestas determinísticas
- ✅ Costo: Tier gratuito generoso
- ✅ Calidad: Llama-3.3-70b es muy capaz

### Vector Store

- **Motor**: FAISS (CPU)
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Dimensión**: 384
- **Documentos**: 6054 chunks
- **Chunk size**: 1000 caracteres
- **Overlap**: 200 caracteres

### Estrategias de Orquestación

El orchestrator decide automáticamente:

| Estrategia | Intención | Docs | Modo |
|------------|-----------|------|------|
| `direct_response` | general | 0 | none |
| `simple_rag` | busqueda | 5 | standard |
| `comparison_rag` | comparacion | 6 | comparison |
| `summary_rag` | resumen | 8 | summary |

## 🎯 Métricas de Rendimiento

**Tiempos promedio** (en test con 10 casos):
- Clasificación: ~1.5s
- Recuperación: ~2.5s
- Generación: ~3s
- Validación: ~2.5s
- **Total**: ~10s por consulta

**Calidad**:
- Validación exitosa: ~90%
- Regeneraciones necesarias: ~10%
- Fuentes citadas: 100%

## 📝 Trazabilidad

Cada consulta genera:

1. **Log detallado** (`logs/test_dinosaurios.log`):
   - Timestamps de cada paso
   - Decisiones del orchestrator
   - Llamadas a LLM
   - Resultados de validación

2. **Caso de uso JSON** (`results/casos_de_uso/caso_X.json`):
   ```json
   {
     "query": "...",
     "intent": "busqueda",
     "strategy": "simple_rag",
     "documents": 5,
     "response": "...",
     "validation_score": 0.9,
     "metadata": {...}
   }
   ```

3. **Batch completo** (`results/respuestas/test_dinosaurios_TIMESTAMP.json`):
   - Todos los casos de una ejecución
   - Estadísticas agregadas
   - Distribución de intenciones

## 📖 Documentación Adicional

- `/docs/ARCHITECTURE.md` - Arquitectura detallada
- `/docs/AUTONOMOUS_AGENTS_GUIDE.md` - Guía de agentes
- `/docs/USAGE_GUIDE.md` - Guía de uso completa
- `/docs/PROMPTS_REFERENCE.md` - Referencia de prompts

## 🐛 Troubleshooting

### Error: Vector store no encontrado
```bash
# El índice ya existe en data/vectorstore/faiss_index/
# Si es necesario reindexar:
python main.py --index
```

### Error: API Key inválida
```bash
# Verifica .env:
GROQ_API_KEY=gsk_...
```

### Error: Rate limiting
El sistema ya incluye delays de 1.5s entre llamadas. Si aún así tienes problemas, aumenta `API_DELAY` en los archivos de agentes.

### Tests fallan
```bash
# Verifica dependencias:
pip install -r requirements.txt --upgrade

# Verifica que el vector store existe:
ls data/vectorstore/faiss_index/
```

## 👥 Equipo

**Práctica 3 - Procesamiento de Lenguaje Natural**

Sistema RAG autónomo con 4 agentes especializados, implementado con LangChain 1.1 y Groq LLM.

## 🚀 Próximos Pasos

- [ ] Interfaz de chat interactivo
- [ ] Soporte multimodal (imágenes de dinosaurios)
- [ ] Comparación con otros LLMs
- [ ] Expansión a otros dominios

## 📄 Licencia

MIT License

## 🔗 Referencias

- [LangChain 1.1](https://python.langchain.com/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [Sentence Transformers](https://www.sbert.net/)
- [Groq](https://groq.com/)
- [Streamlit](https://streamlit.io/)

---

**Última actualización**: Diciembre 2025  
**Dataset**: 100+ documentos científicos sobre dinosaurios  
**Vector Store**: 6054 chunks indexados  
**LLM**: Groq Llama-3.3-70b-versatile