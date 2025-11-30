"""
Tool para logging estructurado.
PENDIENTE DE IMPLEMENTACIÓN: Persona 2/3
"""
import logging

logger = logging.getLogger(__name__)


class LoggerTool:
    """
    Herramienta para logging.
    
    TODO (Persona 2/3): Implementar sistema de logging
    """
    
    name = "logger"
    description = "Sistema de logging estructurado"
    
    @staticmethod
    def log_event(event: str, level: str = "INFO"):
        """Registra un evento. TODO: Implementar"""
        logger.warning("LoggerTool - PENDIENTE DE IMPLEMENTACIÓN")
