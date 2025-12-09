"""
Tool para exportar trazas y resultados del sistema.
Exporta casos de uso individuales y resultados batch en formato JSON/Markdown.
"""
import json
import logging
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class TraceExporterTool:
    """
    Herramienta para exportar trazas de ejecución y resultados.
    
    Funcionalidades:
    - Exportar casos de uso individuales con trazabilidad completa
    - Exportar resultados de procesamiento batch
    - Generar reportes en JSON y Markdown
    - Organizar exports por fecha y dominio
    """
    
    name = "trace_exporter"
    description = "Exporta trazas de ejecución y resultados del sistema"
    
    @staticmethod
    def export_case_study(
        case_number: int,
        query: str,
        response: str,
        trace_data: Dict[str, Any],
        domain: str = "general"
    ) -> str:
        """
        Exporta un caso de uso individual con toda su trazabilidad.
        
        Args:
            case_number: Número del caso de uso
            query: Consulta del usuario
            response: Respuesta generada
            trace_data: Datos de trazabilidad del flujo
            domain: Dominio del caso (salud, legal, etc.)
            
        Returns:
            Ruta del archivo exportado
        """
        try:
            # Crear directorio de resultados
            results_dir = Path("results/casos_de_uso")
            results_dir.mkdir(parents=True, exist_ok=True)
            
            # Timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Datos del caso de uso
            case_data = {
                "case_number": case_number,
                "timestamp": timestamp,
                "domain": domain,
                "query": query,
                "response": response,
                "trace": trace_data,
                "metadata": {
                    "intent": trace_data.get("intent"),
                    "documents_used": trace_data.get("documents_used", 0),
                    "execution_time": trace_data.get("execution_time", 0),
                    "agents_called": trace_data.get("agents_called", []),
                    "tools_used": trace_data.get("tools_used", [])
                }
            }
            
            # Exportar JSON
            json_file = results_dir / f"caso_{case_number}_{domain}_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(case_data, f, ensure_ascii=False, indent=2)
            
            # Exportar Markdown
            md_file = results_dir / f"caso_{case_number}_{domain}_{timestamp}.md"
            markdown_content = TraceExporterTool._generate_case_markdown(case_data)
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logger.info(f"Caso de uso #{case_number} exportado: {json_file}")
            return str(json_file)
            
        except Exception as e:
            logger.error(f"Error exportando caso de uso: {str(e)}")
            return ""
    
    @staticmethod
    def export_batch_results(
        results: List[Dict[str, Any]],
        batch_name: str = "batch"
    ) -> str:
        """
        Exporta resultados de procesamiento batch.
        
        Args:
            results: Lista de resultados de consultas
            batch_name: Nombre del batch
            
        Returns:
            Ruta del archivo exportado
        """
        try:
            # Crear directorio de resultados
            results_dir = Path("results/respuestas")
            results_dir.mkdir(parents=True, exist_ok=True)
            
            # Timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Datos del batch
            batch_data = {
                "batch_name": batch_name,
                "timestamp": timestamp,
                "total_queries": len(results),
                "results": results,
                "summary": {
                    "total_documents_used": sum(r.get("documents_used", 0) for r in results),
                    "average_execution_time": sum(r.get("execution_time", 0) for r in results) / len(results) if results else 0,
                    "intents": {},
                    "strategies": {}
                }
            }
            
            # Calcular estadísticas
            for result in results:
                intent = result.get("intent", "unknown")
                strategy = result.get("strategy", "unknown")
                
                batch_data["summary"]["intents"][intent] = batch_data["summary"]["intents"].get(intent, 0) + 1
                batch_data["summary"]["strategies"][strategy] = batch_data["summary"]["strategies"].get(strategy, 0) + 1
            
            # Exportar JSON
            json_file = results_dir / f"{batch_name}_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(batch_data, f, ensure_ascii=False, indent=2)
            
            # Exportar Markdown
            md_file = results_dir / f"{batch_name}_{timestamp}.md"
            markdown_content = TraceExporterTool._generate_batch_markdown(batch_data)
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logger.info(f"Batch '{batch_name}' exportado: {json_file}")
            return str(json_file)
            
        except Exception as e:
            logger.error(f"Error exportando batch: {str(e)}")
            return ""
    
    @staticmethod
    def export_trace(trace_data: Dict[str, Any], format: str = "json") -> str:
        """
        Exporta una traza individual.
        
        Args:
            trace_data: Datos de la traza
            format: Formato de exportación (json o markdown)
            
        Returns:
            Ruta del archivo exportado
        """
        try:
            # Crear directorio de trazas
            traces_dir = Path("results/trazas")
            traces_dir.mkdir(parents=True, exist_ok=True)
            
            # Timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = trace_data.get("session_id", "unknown")
            
            # Exportar según formato
            if format == "json":
                file_path = traces_dir / f"trace_{session_id}_{timestamp}.json"
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(trace_data, f, ensure_ascii=False, indent=2)
            else:  # markdown
                file_path = traces_dir / f"trace_{session_id}_{timestamp}.md"
                markdown_content = TraceExporterTool._generate_trace_markdown(trace_data)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
            
            logger.info(f"Traza exportada: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error exportando traza: {str(e)}")
            return ""
    
    @staticmethod
    def _generate_case_markdown(case_data: Dict[str, Any]) -> str:
        """Genera contenido Markdown para un caso de uso."""
        md = f"""# Caso de Uso #{case_data['case_number']} - {case_data['domain'].upper()}

**Fecha:** {case_data['timestamp']}

---

## 📝 Consulta

```
{case_data['query']}
```

---

## 💬 Respuesta

{case_data['response']}

---

## 📊 Metadata

- **Intención:** {case_data['metadata'].get('intent', 'N/A')}
- **Documentos utilizados:** {case_data['metadata'].get('documents_used', 0)}
- **Tiempo de ejecución:** {case_data['metadata'].get('execution_time', 0):.2f}s
- **Agentes llamados:** {', '.join(case_data['metadata'].get('agents_called', []))}
- **Tools utilizadas:** {', '.join(case_data['metadata'].get('tools_used', []))}

---

## 🔍 Trazabilidad

```json
{json.dumps(case_data['trace'], ensure_ascii=False, indent=2)}
```
"""
        return md
    
    @staticmethod
    def _generate_batch_markdown(batch_data: Dict[str, Any]) -> str:
        """Genera contenido Markdown para resultados batch."""
        md = f"""# Resultados Batch: {batch_data['batch_name']}

**Fecha:** {batch_data['timestamp']}
**Total de consultas:** {batch_data['total_queries']}

---

## 📊 Resumen

- **Total documentos consultados:** {batch_data['summary']['total_documents_used']}
- **Tiempo promedio:** {batch_data['summary']['average_execution_time']:.2f}s

### Distribución de Intenciones
"""
        for intent, count in batch_data['summary']['intents'].items():
            md += f"- **{intent}:** {count}\n"
        
        md += "\n### Distribución de Estrategias\n"
        for strategy, count in batch_data['summary']['strategies'].items():
            md += f"- **{strategy}:** {count}\n"
        
        md += "\n---\n\n## 📋 Resultados Individuales\n\n"
        
        for i, result in enumerate(batch_data['results'], 1):
            md += f"""### Consulta {i}

**Query:** {result.get('query', 'N/A')}

**Intent:** {result.get('intent', 'N/A')} | **Strategy:** {result.get('strategy', 'N/A')} | **Docs:** {result.get('documents_used', 0)}

**Respuesta:**
```
{result.get('response', 'N/A')[:200]}...
```

---

"""
        
        return md
    
    @staticmethod
    def _generate_trace_markdown(trace_data: Dict[str, Any]) -> str:
        """Genera contenido Markdown para una traza."""
        md = f"""# Traza de Ejecución

**Session ID:** {trace_data.get('session_id', 'N/A')}

---

## Pasos Ejecutados

"""
        for i, step in enumerate(trace_data.get('steps', []), 1):
            md += f"### Paso {i}\n"
            md += f"- **Agent:** {step.get('agent', 'N/A')}\n"
            md += f"- **Action:** {step.get('action', 'N/A')}\n"
            md += f"- **Result:** {step.get('result', {})}\n\n"
        
        return md

