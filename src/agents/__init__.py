"""
Módulo de agentes del sistema.

IMPORTANTE: Ahora hay dos versiones de agentes:

1. AGENTES CLÁSICOS (Originales):
   - ClassifierAgent, RetrieverAgent, RAGAgent, CriticAgent, Orchestrator
   - Usan LLMs con salida estructurada
   - Flujo guiado por código Python
   - Sin uso de @tool de LangChain

2. AGENTES AUTÓNOMOS (Nuevos):
   - AutonomousClassifierAgent, AutonomousRetrieverAgent, etc.
   - Usan LangChain tool calling
   - Deciden autónomamente cuándo usar tools
   - Sistema verdaderamente agentic

Recomendación: Usar los agentes autónomos para mayor flexibilidad.
"""
import logging

# Agentes clásicos (originales)
from .classifier_agent import ClassifierAgent
from .retriever_agent import RetrieverAgent
from .rag_agent import RAGAgent
from .critic_agent import CriticAgent
from .orchestrator import Orchestrator

# Agentes autónomos (con tools)
from .autonomous_classifier_agent import AutonomousClassifierAgent
from .autonomous_retriever_agent import AutonomousRetrieverAgent
from .autonomous_rag_agent import AutonomousRAGAgent
from .autonomous_critic_agent import AutonomousCriticAgent
from .autonomous_orchestrator import AutonomousOrchestrator

# Agente indexador
from .indexer_agent import IndexerAgent  # Clásico
from .autonomous_indexer_agent import AutonomousIndexerAgent  # Autónomo

logger = logging.getLogger(__name__)

__all__ = [
    # Agentes clásicos
    'ClassifierAgent',
    'RetrieverAgent',
    'RAGAgent',
    'CriticAgent',
    'Orchestrator',
    'IndexerAgent',
    
    # Agentes autónomos
    'AutonomousClassifierAgent',
    'AutonomousRetrieverAgent',
    'AutonomousRAGAgent',
    'AutonomousCriticAgent',
    'AutonomousOrchestrator',
    'AutonomousIndexerAgent',
]

logger.info("Agentes disponibles: 6 clásicos + 6 autónomos")
