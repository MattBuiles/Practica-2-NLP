"""
Módulo de agentes del sistema.

Sistema de Agentes Autónomos con LangChain:
- AutonomousClassifierAgent, AutonomousRetrieverAgent, etc.
- Usan LangChain tool calling
- Deciden autónomamente cuándo usar tools
- Sistema verdaderamente agentic
"""
import logging

# Agentes autónomos (con tools)
from .autonomous_classifier_agent import AutonomousClassifierAgent
from .autonomous_retriever_agent import AutonomousRetrieverAgent
from .autonomous_rag_agent import AutonomousRAGAgent
from .autonomous_critic_agent import AutonomousCriticAgent
from .autonomous_orchestrator import AutonomousOrchestrator

# Agente indexador autónomo
from .autonomous_indexer_agent import AutonomousIndexerAgent

logger = logging.getLogger(__name__)

__all__ = [
    # Agentes autónomos
    'AutonomousClassifierAgent',
    'AutonomousRetrieverAgent',
    'AutonomousRAGAgent',
    'AutonomousCriticAgent',
    'AutonomousOrchestrator',
    'AutonomousIndexerAgent',
]

logger.info("Agentes autónomos cargados correctamente")

