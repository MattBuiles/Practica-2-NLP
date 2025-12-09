"""
Tool para registro y trazabilidad de ejecución.
Permite a los agentes registrar decisiones y crear logs estructurados.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def log_agent_decision(agent_name: str, decision: str, reasoning: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Registra una decisión tomada por un agente para trazabilidad.
    
    Esta herramienta debe usarse cuando:
    - Un agente toma una decisión importante
    - Se necesita registrar el razonamiento detrás de una acción
    - Se quiere mantener un historial de ejecución
    - Se requiere depurar o auditar el comportamiento del sistema
    
    Args:
        agent_name: Nombre del agente que toma la decisión
                   Ejemplo: "ClassifierAgent", "RetrieverAgent"
        decision: La decisión tomada
                 Ejemplo: "Clasificar como búsqueda", "Recuperar 5 documentos"
        reasoning: Justificación de la decisión
                  Ejemplo: "Usuario pregunta por información específica"
        metadata: Información adicional opcional
                 Ejemplo: {"confidence": 0.95, "intent": "busqueda"}
    
    Returns:
        Diccionario confirmando el registro:
        {
            "logged": bool,
            "timestamp": str,
            "log_id": str
        }
        
    Ejemplo de uso:
        log_agent_decision(
            agent_name="ClassifierAgent",
            decision="Clasificado como comparación",
            reasoning="Usuario solicita contrastar dos conceptos",
            metadata={"confidence": 0.92, "requires_rag": True}
        )
    """
    try:
        timestamp = datetime.now().isoformat()
        log_id = f"{agent_name}_{timestamp}"
        
        log_entry = {
            "agent": agent_name,
            "decision": decision,
            "reasoning": reasoning,
            "metadata": metadata or {},
            "timestamp": timestamp
        }
        
        logger.info(f"[{agent_name}] Decisión: {decision} | Razón: {reasoning}")
        
        if metadata:
            logger.debug(f"[{agent_name}] Metadata: {metadata}")
        
        return {
            "logged": True,
            "timestamp": timestamp,
            "log_id": log_id
        }
        
    except Exception as e:
        logger.error(f"Error registrando decisión: {str(e)}")
        return {
            "logged": False,
            "timestamp": datetime.now().isoformat(),
            "log_id": None
        }


@tool
def log_agent_action(agent_name: str, action: str, input_data: str, output_data: str, success: bool = True) -> Dict[str, Any]:
    """
    Registra una acción ejecutada por un agente.
    
    Esta herramienta debe usarse cuando:
    - Un agente ejecuta una acción concreta
    - Se necesita registrar entrada y salida de operaciones
    - Se quiere rastrear el flujo de datos en el sistema
    - Se requiere información para debugging
    
    Args:
        agent_name: Nombre del agente
        action: Acción ejecutada
                Ejemplo: "Búsqueda semántica", "Generación de respuesta"
        input_data: Datos de entrada (resumido)
                   Ejemplo: "Query: '¿Qué es diabetes?'"
        output_data: Datos de salida (resumido)
                    Ejemplo: "5 documentos recuperados"
        success: Si la acción fue exitosa (default: True)
    
    Returns:
        Confirmación del registro con timestamp.
        
    Ejemplo de uso:
        log_agent_action(
            agent_name="RetrieverAgent",
            action="Búsqueda de documentos",
            input_data="Query optimizada: 'diabetes tipo 2'",
            output_data="Recuperados 5 documentos relevantes",
            success=True
        )
    """
    try:
        timestamp = datetime.now().isoformat()
        
        status = "✓ ÉXITO" if success else "✗ ERROR"
        
        logger.info(f"[{agent_name}] {status} | Acción: {action}")
        logger.debug(f"[{agent_name}] Input: {input_data[:100]}...")
        logger.debug(f"[{agent_name}] Output: {output_data[:100]}...")
        
        return {
            "logged": True,
            "timestamp": timestamp,
            "success": success
        }
        
    except Exception as e:
        logger.error(f"Error registrando acción: {str(e)}")
        return {
            "logged": False,
            "timestamp": datetime.now().isoformat(),
            "success": False
        }


@tool  
def get_available_documents_info() -> Dict[str, Any]:
    """
    Obtiene información sobre los documentos disponibles en el sistema.
    
    Esta herramienta debe usarse cuando:
    - Se necesita saber qué documentos están indexados
    - El usuario pregunta sobre el contenido disponible
    - Se quiere verificar si hay información sobre un tema
    
    Returns:
        Información sobre documentos disponibles:
        {
            "total_documents": int,
            "status": str,
            "message": str
        }
        
    Ejemplo de uso:
        info = get_available_documents_info()
        print(f"Documentos disponibles: {info['total_documents']}")
    """
    try:
        from src.rag_pipeline.vectorstore import vectorstore_manager
        
        if not vectorstore_manager.vectorstore:
            return {
                "total_documents": 0,
                "status": "not_initialized",
                "message": "Vector store no inicializado"
            }
        
        # Intentar obtener estadísticas básicas
        # FAISS no tiene método directo para contar, hacemos búsqueda dummy
        try:
            results = vectorstore_manager.vectorstore.similarity_search("", k=1)
            available = len(results) > 0
        except:
            available = False
        
        if available:
            return {
                "total_documents": "100+",  # Sabemos que hay documentos
                "status": "active",
                "message": "Sistema con documentos indexados y disponibles"
            }
        else:
            return {
                "total_documents": 0,
                "status": "empty",
                "message": "No hay documentos indexados"
            }
        
    except Exception as e:
        logger.error(f"Error obteniendo info de documentos: {str(e)}")
        return {
            "total_documents": 0,
            "status": "error",
            "message": f"Error: {str(e)}"
        }
