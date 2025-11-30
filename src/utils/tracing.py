"""
Sistema de trazabilidad para el flujo de ejecución del sistema Agentic AI.
Registra todas las decisiones, acciones y resultados de los agentes.
"""
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from src.config.paths import TRACES_DIR


class ExecutionTrace:
    """Representa una traza de ejecución completa."""
    
    def __init__(self, query: str, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.query = query
        self.start_time = datetime.now()
        self.end_time = None
        self.steps: List[Dict[str, Any]] = []
        self.final_response = None
        self.metadata = {
            "total_llm_calls": 0,
            "agents_involved": set(),
            "documents_retrieved": [],
            "regeneration_count": 0
        }
    
    def add_step(self, agent: str, action: str, details: Dict[str, Any]):
        """Añade un paso a la traza de ejecución."""
        step = {
            "step_number": len(self.steps) + 1,
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "details": details
        }
        self.steps.append(step)
        self.metadata["agents_involved"].add(agent)
        
        if "llm_call" in details and details["llm_call"]:
            self.metadata["total_llm_calls"] += 1
    
    def add_classification(self, intent: str, confidence: float, reasoning: str):
        """Registra la clasificación de intención."""
        self.add_step(
            agent="classifier",
            action="classify_intent",
            details={
                "intent": intent,
                "confidence": confidence,
                "reasoning": reasoning,
                "llm_call": True
            }
        )
    
    def add_retrieval(self, documents: List[Dict], query_reformulated: Optional[str] = None):
        """Registra la recuperación de documentos."""
        doc_ids = [doc.get("id", "unknown") for doc in documents]
        self.metadata["documents_retrieved"].extend(doc_ids)
        
        self.add_step(
            agent="retriever",
            action="retrieve_documents",
            details={
                "num_documents": len(documents),
                "document_ids": doc_ids,
                "query_reformulated": query_reformulated,
                "llm_call": query_reformulated is not None
            }
        )
    
    def add_generation(self, response: str, context_used: List[str], citations: List[str]):
        """Registra la generación de respuesta RAG."""
        self.add_step(
            agent="rag",
            action="generate_response",
            details={
                "response_length": len(response),
                "num_context_docs": len(context_used),
                "citations": citations,
                "llm_call": True
            }
        )
    
    def add_validation(self, is_valid: bool, validation_results: Dict, needs_regeneration: bool):
        """Registra la validación del crítico."""
        if needs_regeneration:
            self.metadata["regeneration_count"] += 1
        
        self.add_step(
            agent="critic",
            action="validate_response",
            details={
                "is_valid": is_valid,
                "validation_results": validation_results,
                "needs_regeneration": needs_regeneration,
                "llm_call": True
            }
        )
    
    def add_general_response(self, response: str):
        """Registra respuesta general sin RAG."""
        self.add_step(
            agent="orchestrator",
            action="generate_general_response",
            details={
                "response_length": len(response),
                "llm_call": True
            }
        )
    
    def finalize(self, final_response: str):
        """Finaliza la traza con la respuesta final."""
        self.end_time = datetime.now()
        self.final_response = final_response
        self.metadata["execution_time_seconds"] = (
            self.end_time - self.start_time
        ).total_seconds()
        self.metadata["agents_involved"] = list(self.metadata["agents_involved"])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la traza a diccionario."""
        return {
            "session_id": self.session_id,
            "query": self.query,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "steps": self.steps,
            "final_response": self.final_response,
            "metadata": self.metadata
        }
    
    def save(self, filename: Optional[str] = None):
        """Guarda la traza en un archivo JSON."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trace_{self.session_id}_{timestamp}.json"
        
        filepath = TRACES_DIR / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def get_summary(self) -> str:
        """Genera un resumen legible de la traza."""
        summary = [
            f"=== Resumen de Ejecución ===",
            f"Session ID: {self.session_id}",
            f"Consulta: {self.query}",
            f"Tiempo total: {self.metadata.get('execution_time_seconds', 0):.2f}s",
            f"Agentes involucrados: {', '.join(self.metadata['agents_involved'])}",
            f"Llamadas LLM: {self.metadata['total_llm_calls']}",
            f"Documentos recuperados: {len(self.metadata['documents_retrieved'])}",
            f"Regeneraciones: {self.metadata['regeneration_count']}",
            f"\n=== Pasos Ejecutados ===",
        ]
        
        for step in self.steps:
            summary.append(
                f"{step['step_number']}. [{step['agent']}] {step['action']}"
            )
        
        return "\n".join(summary)


class TraceManager:
    """Gestiona múltiples trazas de ejecución."""
    
    def __init__(self):
        self.traces: Dict[str, ExecutionTrace] = {}
        self.current_trace: Optional[ExecutionTrace] = None
    
    def start_trace(self, query: str, session_id: Optional[str] = None) -> ExecutionTrace:
        """Inicia una nueva traza de ejecución."""
        trace = ExecutionTrace(query, session_id)
        self.traces[trace.session_id] = trace
        self.current_trace = trace
        return trace
    
    def get_trace(self, session_id: str) -> Optional[ExecutionTrace]:
        """Obtiene una traza por su ID."""
        return self.traces.get(session_id)
    
    def end_trace(self, session_id: str, final_response: str):
        """Finaliza una traza."""
        trace = self.traces.get(session_id)
        if trace:
            trace.finalize(final_response)
            trace.save()
    
    def get_all_traces(self) -> List[ExecutionTrace]:
        """Obtiene todas las trazas."""
        return list(self.traces.values())


# Instancia global del gestor de trazas
trace_manager = TraceManager()
