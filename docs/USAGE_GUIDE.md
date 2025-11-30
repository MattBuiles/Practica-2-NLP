# Guía de Uso del Sistema Agentic AI

## 🚀 Inicio Rápido (5 minutos)

### 1. Configuración Inicial

```bash
# Clonar e instalar
git clone <repo-url>
cd Practica-2-NLP
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Configurar API Keys

Crear archivo `.env`:
```env
GOOGLE_API_KEY=tu_google_api_key
GROQ_API_KEY=tu_groq_api_key
```

### 3. Preparar Documentos

```bash
# Copiar tus documentos a:
data/raw/
```

Formatos soportados: PDF, HTML, TXT

### 4. Indexar

```bash
python main.py --index
```

### 5. ¡Listo para usar!

```bash
python main.py
```

---

## 📖 Uso Detallado

### Modo Interactivo

El modo más común para exploración:

```bash
python main.py
# o
python main.py --interactive
```

**Tipos de consultas que puedes hacer**:

1. **Búsqueda de información**:
   - "¿Qué es la diabetes?"
   - "Explica los síntomas del asma"
   - "Dame información sobre tratamientos del cáncer"

2. **Resúmenes**:
   - "Resume el documento sobre hipertensión"
   - "Hazme un resumen de los tratamientos disponibles"
   - "Resume los principales factores de riesgo"

3. **Comparaciones**:
   - "Compara diabetes tipo 1 y tipo 2"
   - "Diferencias entre paracetamol e ibuprofeno"
   - "Compara los tratamientos A y B"

4. **Generales** (sin RAG):
   - "Hola, ¿cómo estás?"
   - "Cuéntame un chiste"
   - "¿Qué día es hoy?"

### Modo Batch

Para procesar múltiples consultas de una vez:

1. Crear archivo `queries.txt`:
```
¿Qué es la hipertensión?
Resume los síntomas de la diabetes
Compara tratamiento A con B
```

2. Ejecutar:
```bash
python main.py --batch queries.txt
```

3. Resultados en: `results/respuestas/`

### Exportar Casos de Uso

Durante el modo interactivo, después de cada respuesta:

```
💾 ¿Exportar como caso de uso? (s/n): s
```

Se guardará en:
- JSON: `results/casos_de_uso/caso_01_salud.json`
- Markdown: `results/casos_de_uso/caso_01_salud.md`

---

## 🔧 Configuración Avanzada

### Ajustar Parámetros de Chunking

Editar `src/config/settings.yaml`:

```yaml
embeddings:
  chunk_size: 1000      # Cambiar tamaño
  chunk_overlap: 200    # Cambiar overlap
```

Luego re-indexar:
```bash
python main.py --index
```

### Cambiar Número de Documentos Recuperados

En `settings.yaml`:
```yaml
faiss:
  top_k: 5  # Cambiar a 3, 10, etc.
```

### Ajustar Criterios de Validación

En `settings.yaml`:
```yaml
agents:
  critic:
    max_regeneration_attempts: 2  # Cambiar intentos
```

### Usar Directorio Personalizado

```bash
python main.py --index-path "C:\mis_documentos"
```

---

## 📊 Interpretando Resultados

### Metadata de Respuesta

Cada respuesta incluye:

```python
{
    "response": "La respuesta formateada...",
    "intent": "busqueda",           # Intención detectada
    "documents_found": 5,            # Documentos consultados
    "sources": [...],                # Fuentes citadas
    "validation": {...},             # Scores de validación
    "regeneration_attempts": 0,      # Veces regenerado
    "trace": {...}                   # Traza completa
}
```

### Scores de Validación

```python
"validation": {
    "overall_score": 0.85,          # Score general (0-1)
    "is_valid": true,               # ¿Pasó validación?
    "criteria": {
        "coherence": 0.9,
        "context_alignment": 0.8,
        "hallucination_detection": 0.9,
        "completeness": 0.8
    },
    "issues": []                    # Problemas detectados
}
```

**Interpretación**:
- `> 0.8`: Excelente
- `0.6 - 0.8`: Aceptable
- `< 0.6`: Regeneración necesaria

### Traza de Ejecución

La traza muestra el flujo completo:

```
1. [CLASSIFIER] classify_intent
   - intent: busqueda
   - confidence: 0.95

2. [RETRIEVER] retrieve_documents
   - num_documents: 5
   - query_reformulated: "diabetes síntomas tratamiento"

3. [RAG] generate_response
   - response_length: 450
   - num_context_docs: 5

4. [CRITIC] validate_response
   - is_valid: true
   - overall_score: 0.85
```

---

## 🎯 Casos de Uso Comunes

### 1. Análisis de Literatura Médica

```python
from src.agents.orchestrator import Orchestrator

orchestrator = Orchestrator()

# Búsqueda
result = orchestrator.process_query(
    "¿Cuáles son los últimos avances en tratamiento de diabetes?"
)

# Resumen
result = orchestrator.process_query(
    "Resume los hallazgos del estudio sobre hipertensión"
)

# Comparación
result = orchestrator.process_query(
    "Compara efectividad de tratamientos A vs B"
)
```

### 2. Sistema de Q&A

```python
# Cargar índice una vez
pipeline = RAGPipeline()
pipeline.load_existing_index()

orchestrator = Orchestrator()

# Múltiples consultas
queries = ["pregunta 1", "pregunta 2", "pregunta 3"]
results = orchestrator.process_batch(queries)
```

### 3. Generación de Reportes

```python
from src.tools.trace_exporter import TraceExporterTool

# Procesar consulta
result = orchestrator.process_query(query)

# Exportar para reporte
TraceExporterTool.export_case_study(
    case_number=1,
    query=query,
    response=result['response'],
    trace_data=result['trace'],
    domain="salud"
)
```

---

## 🐛 Solución de Problemas

### Error: "No se pudo cargar el índice"

**Causa**: No se han indexado documentos

**Solución**:
```bash
# Verificar que hay documentos en data/raw/
ls data/raw/

# Indexar
python main.py --index
```

### Error: "GOOGLE_API_KEY no encontrada"

**Causa**: Falta archivo `.env`

**Solución**:
```bash
# Copiar ejemplo
cp .env.example .env

# Editar y añadir tus keys
# GOOGLE_API_KEY=tu_key_aqui
# GROQ_API_KEY=tu_key_aqui
```

### Error: Import "langchain" could not be resolved

**Causa**: Dependencias no instaladas

**Solución**:
```bash
pip install -r requirements.txt
```

### Respuestas de baja calidad

**Posibles causas y soluciones**:

1. **Documentos insuficientes**:
   - Añade más documentos (mín. 100)
   
2. **Chunks muy grandes/pequeños**:
   - Ajusta `chunk_size` en settings.yaml
   
3. **Pocos documentos recuperados**:
   - Aumenta `top_k` en settings.yaml

4. **Consulta ambigua**:
   - Reformula la pregunta con más contexto

### Sistema lento

**Optimizaciones**:

1. **Usar GPU para embeddings**:
   ```python
   # En embeddings.py
   model_kwargs={'device': 'cuda'}
   ```

2. **Reducir documentos recuperados**:
   ```yaml
   # settings.yaml
   top_k: 3  # En lugar de 5
   ```

3. **Chunks más grandes**:
   ```yaml
   chunk_size: 1500  # En lugar de 1000
   ```

---

## 📈 Mejores Prácticas

### 1. Preparación de Documentos

✅ **Hacer**:
- Usar documentos relevantes al dominio
- Mínimo 100 documentos
- Formatos limpios (PDFs bien estructurados)
- Nombres descriptivos de archivos

❌ **Evitar**:
- PDFs escaneados sin OCR
- Documentos duplicados
- Archivos corruptos
- Mezclar dominios muy diferentes

### 2. Consultas Efectivas

✅ **Hacer**:
- Ser específico: "¿Cuáles son los síntomas de diabetes tipo 2?"
- Usar vocabulario del dominio
- Indicar tipo de respuesta: "Resume...", "Compara..."

❌ **Evitar**:
- Consultas muy vagas: "Dime sobre salud"
- Múltiples preguntas en una
- Lenguaje coloquial excesivo

### 3. Validación de Resultados

✅ **Siempre revisar**:
- Score de validación
- Fuentes citadas
- Issues detectados
- Número de regeneraciones

✅ **Exportar casos importantes**:
- Para documentación
- Para evaluación
- Para mejora del sistema

### 4. Mantenimiento

✅ **Regularmente**:
- Actualizar documentos
- Re-indexar después de cambios
- Revisar logs en `logs/system_logs/`
- Analizar trazas en `logs/traces/`

---

## 🎓 Para la Sustentación

### Demostración Recomendada

1. **Mostrar arquitectura** (2 min):
   - Diagrama de flujo
   - Agentes y sus roles
   
2. **Indexación** (1 min):
   ```bash
   python main.py --index
   ```

3. **Casos de uso variados** (5 min):
   - Búsqueda: "¿Qué es X?"
   - Resumen: "Resume documento Y"
   - Comparación: "Compara A con B"
   - General: "Hola"

4. **Mostrar trazabilidad** (1 min):
   - Abrir trace JSON/Markdown
   - Explicar flujo de decisión

5. **Validación** (1 min):
   - Mostrar scores
   - Explicar criterios
   - Demostrar regeneración

### Preguntas Frecuentes

**P: ¿Por qué Gemini y Groq?**
R: Gemini para razonamiento profundo (clasificar, validar), Groq para velocidad (recuperar, generar)

**P: ¿Cómo garantizan calidad?**
R: Agente crítico valida con 5 criterios + regeneración automática

**P: ¿Escala a más documentos?**
R: Sí, FAISS es eficiente. Probado con 100+ documentos.

**P: ¿Funciona en otros dominios?**
R: Sí, solo cambiar documentos y re-indexar

---

## 📚 Recursos Adicionales

- **Documentación completa**: `docs/ARCHITECTURE.md`
- **Ejemplos**: `examples.py`
- **Logs**: `logs/system_logs/`
- **Trazas**: `logs/traces/`
- **Casos de uso**: `results/casos_de_uso/`

---

## 🤝 Contribuir

Para añadir nuevos agentes:

1. Crear en `src/agents/nuevo_agent.py`
2. Implementar interfaz estándar
3. Registrar en `orchestrator.py`
4. Actualizar documentación

Para nuevas tools:

1. Crear en `src/tools/nueva_tool.py`
2. Heredar de clase base (si existe)
3. Documentar uso
4. Añadir tests

---

## ✅ Checklist Pre-Sustentación

- [ ] Documentos indexados (mín. 100)
- [ ] API keys configuradas
- [ ] Sistema funciona en modo interactivo
- [ ] Al menos 10 casos de uso exportados
- [ ] Logs y trazas revisadas
- [ ] README actualizado
- [ ] Ejemplos funcionan
- [ ] Diagrama de arquitectura listo
- [ ] PowerPoint preparado
- [ ] Respuestas a preguntas frecuentes ensayadas

---

**¡Éxito en tu sustentación! 🚀**
