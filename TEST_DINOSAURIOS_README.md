# Test de Dinosaurios - Guía de Uso

## 📋 Descripción

El archivo `test_dinosaurios.py` es un script de prueba completo que ejecuta 10 casos de uso sobre el sistema RAG con el dataset de dinosaurios. El test verifica:

- ✅ Funcionamiento del sistema RAG
- ✅ Registro de trazas en la carpeta `logs/`
- ✅ Guardado de resultados en la carpeta `results/`

## 🚀 Requisitos Previos

1. **Variables de entorno configuradas**:
   - `GOOGLE_API_KEY`
   - `GROQ_API_KEY`

2. **Vectorstore indexado**:
   ```bash
   python main.py --index
   ```

## 📁 Estructura de Salida

El test genera archivos en las siguientes ubicaciones:

### Logs (`logs/`)
- `test_dinosaurios.log` - Log del test con todas las operaciones
- `system.log` - Log del sistema principal

### Resultados (`results/`)
```
results/
├── casos_de_uso/
│   ├── caso_01_dinosaurios_*.json
│   ├── caso_02_dinosaurios_*.json
│   └── ... (uno por cada caso)
├── respuestas/
│   └── batch_test_dinosaurios_*.json
└── test_dinosaurios_summary.json
```

## 🎯 Casos de Uso Incluidos

1. **Información General** - Dinosaurios más grandes
2. **Anatomía y Características** - Brazos del T-Rex
3. **Evolución** - Aves desde dinosaurios
4. **Comportamiento** - Dinosaurios como padres
5. **Extinción** - Asteroide y extinción masiva
6. **Especies Específicas** - Spinosaurus
7. **Fósiles y Descubrimientos** - Huellas de dinosaurio
8. **Anatomía Comparativa** - Stegosaurus vs Ankylosaurus
9. **Paleontología Moderna** - Preparación de fósiles
10. **Cronología** - Períodos de los dinosaurios

## 🏃 Ejecución

### Método 1: Ejecución Directa
```bash
python test_dinosaurios.py
```

### Método 2: Usando pytest (si está disponible)
```bash
pytest test_dinosaurios.py -v
```

## 📊 Salida del Test

### Durante la Ejecución
El test muestra en tiempo real:
- Verificación del entorno
- Progreso de cada caso de uso
- Respuestas generadas
- Metadata (estrategia, tiempo, validación)

### Al Finalizar
```
📊 REPORTE FINAL - TEST DE DINOSAURIOS
===============================================
✅ Casos exitosos: 10/10
❌ Casos con error: 0/10

📈 Estadísticas:
   - Tiempo promedio: 5.23s
   - Documentos promedio: 3.4

🎯 Distribución de Intenciones:
   - simple_query: 6
   - comparison: 2
   - specific_document: 2

🔧 Distribución de Estrategias:
   - simple_rag: 7
   - comparison_rag: 2
   - document_rag: 1

✓ Casos validados exitosamente: 9/10
```

### Verificación de Archivos
Al final, el test verifica automáticamente:
- ✅ Logs generados en `logs/`
- ✅ Casos de uso guardados en `results/casos_de_uso/`
- ✅ Resultados batch en `results/respuestas/`
- ✅ Resumen del test en `results/test_dinosaurios_summary.json`

## 🔍 Verificación Manual

Después de ejecutar el test, puedes verificar:

```bash
# Ver logs generados
ls logs/

# Ver casos de uso generados
ls results/casos_de_uso/

# Ver resumen del test
cat results/test_dinosaurios_summary.json
```

## 📝 Formato de Resultados

### Archivo de Caso Individual
```json
{
  "caso_numero": 1,
  "timestamp": "2025-12-09T10:30:00",
  "query": "¿Cuáles fueron los dinosaurios más grandes?",
  "response": "...",
  "trace": {
    "intent": "simple_query",
    "strategy": "simple_rag",
    "execution_time": 4.5,
    "documents_used": 3
  }
}
```

### Resumen del Test
```json
{
  "timestamp": "2025-12-09T10:35:00",
  "total_casos": 10,
  "resultados": [
    {
      "caso": 1,
      "categoria": "Información General",
      "query": "...",
      "response": "...",
      "intent": "simple_query",
      "strategy": "simple_rag",
      "execution_time": 4.5,
      "validation_passed": true
    }
  ]
}
```

## ⚠️ Solución de Problemas

### Error: "GOOGLE_API_KEY no configurada"
```bash
# Configura las variables de entorno en .env
GOOGLE_API_KEY=tu_clave_aqui
GROQ_API_KEY=tu_clave_aqui
```

### Error: "No se encontró vectorstore"
```bash
# Indexa los documentos primero
python main.py --index
```

### Error: "No se generaron logs"
- Verifica permisos de escritura en la carpeta `logs/`
- Asegúrate de que el directorio existe

### Advertencia: "No se encontraron archivos batch"
- Esto es normal si `TraceExporterTool.export_batch_results()` no se ejecutó
- El test sigue siendo válido

## 🎓 Notas Adicionales

- El test incluye pausas de 1 segundo entre casos para evitar sobrecarga
- Cada caso se registra individualmente en los logs
- Los códigos de salida son:
  - `0` - Test exitoso con todos los archivos generados
  - `1` - Test con advertencias (algunos archivos faltantes)

## 🔗 Integración con Main

El test utiliza directamente las funciones del sistema principal:
- `AutonomousOrchestrator` para procesar queries
- `TraceExporterTool` para exportar resultados
- Configuración de logging del sistema

Esto asegura que el test evalúa el comportamiento real del sistema en producción.
