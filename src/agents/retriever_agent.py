"""
Agente Recuperador Semántico.
Implementación: Persona 3

Responsabilidades:
- Optimizar consultas usando LLM para mejorar recuperación
- Consultar FAISS (asume que vectorstore_manager está implementado por Persona 2)
- Rankear y filtrar resultados según relevancia
- Proporcionar métodos especializados según intención (búsqueda, comparación, resumen)
"""
import logging
from typing import List, Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.config.llm_config import llm_config
from src.rag_pipeline.vectorstore import vectorstore_manager

logger = logging.getLogger(__name__)


class OptimizedQuery(BaseModel):
    """Modelo para query optimizada por LLM."""
    optimized_query: str = Field(description="Query optimizada para búsqueda semántica")
    keywords: List[str] = Field(description="Palabras clave extraídas")
    reasoning: str = Field(description="Razonamiento de la optimización")


class RetrieverAgent:
    """
    Agente de Recuperación Semántica.
    
    Estrategia:
    1. Optimización de consultas con LLM (Groq) para mejorar recuperación
    2. Consulta al vector store FAISS (implementado por Persona 2)
    3. Ranking y filtrado de resultados por score threshold
    4. Métodos especializados según tipo de intención
    
    Nota: Este agente NO implementa el vector store, solo lo consulta.
    La implementación de FAISS es responsabilidad de Persona 2.
    """
    
    def __init__(self, vectorstore_manager_instance=None):
        """
        Inicializa el agente recuperador.
        
        Args:
            vectorstore_manager_instance: Instancia del vectorstore (opcional).
                                         Por defecto usa la instancia global de Persona 2.
        """
        logger.info("Inicializando RetrieverAgent...")
        
        # Usar instancia proporcionada o la global (de Persona 2)
        self.vectorstore_manager = vectorstore_manager_instance or vectorstore_manager
        
        # LLM para optimización de consultas (Groq - baja latencia)
        self.llm = llm_config.get_retriever_llm()
        self.structured_llm = self.llm.with_structured_output(OptimizedQuery)
        
        # Prompts para optimización de queries
        self.optimization_prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_optimization_system_prompt()),
            ("user", "Query original: {query}\nIntención: {intent}")
        ])
        
        logger.info("RetrieverAgent inicializado correctamente")
    
    def _get_optimization_system_prompt(self) -> str:
        """
        Genera el prompt del sistema para optimización de queries.
        
        El objetivo es reformular la consulta del usuario para maximizar
        la recuperación semántica de documentos relevantes.
        """
        return """Eres un experto en optimización de consultas para búsqueda semántica.

Tu tarea es reformular la consulta del usuario para mejorar la recuperación de documentos relevantes en un sistema RAG.

OBJETIVOS:
1. Expandir la consulta con sinónimos y términos relacionados
2. Eliminar ambigüedades y palabras no informativas
3. Mantener la intención original del usuario
4. Extraer palabras clave principales

ESTRATEGIAS SEGÚN INTENCIÓN:
- busqueda: Enfocarse en términos específicos y precisos
- resumen: Ampliar a términos más generales del dominio
- comparacion: Incluir ambos conceptos a comparar explícitamente
- general: Mantener la consulta simple

EJEMPLO:
Query: "qué dice sobre covid"
Optimizada: "información efectos síntomas tratamiento covid-19 coronavirus pandemia"
Keywords: ["covid-19", "coronavirus", "síntomas", "tratamiento"]

Responde SOLO con los campos del modelo OptimizedQuery."""
    
    def _optimize_query(self, query: str, intent: str = "busqueda") -> Dict[str, Any]:
        """
        Optimiza la consulta del usuario usando LLM.
        
        Args:
            query: Consulta original del usuario
            intent: Intención clasificada (busqueda, resumen, comparacion, general)
        
        Returns:
            Diccionario con query optimizada, keywords y reasoning
        """
        try:
            logger.info(f"Optimizando query con LLM - Intent: {intent}")
            
            messages = self.optimization_prompt.format_messages(
                query=query,
                intent=intent
            )
            
            result = self.structured_llm.invoke(messages)
            
            optimized_data = {
                "optimized_query": result.optimized_query,
                "keywords": result.keywords,
                "reasoning": result.reasoning
            }
            
            logger.info(f"Query optimizada: '{result.optimized_query[:100]}...'")
            return optimized_data
            
        except Exception as e:
            logger.error(f"Error en optimización de query: {str(e)}")
            # Fallback: usar query original
            return {
                "optimized_query": query,
                "keywords": query.split(),
                "reasoning": "Fallback - usando query original por error en optimización"
            }
    
    def _rank_and_filter(self, 
                         documents: List[Dict[str, Any]], 
                         score_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Rankea y filtra documentos por score de similitud.
        
        Args:
            documents: Lista de documentos con scores
            score_threshold: Umbral mínimo de score (None = no filtrar)
        
        Returns:
            Documentos filtrados y ordenados por relevancia
        """
        if not documents:
            return []
        
        # Filtrar por threshold si se especifica
        if score_threshold is not None:
            filtered_docs = [
                doc for doc in documents 
                if doc.get('score', 0) >= score_threshold
            ]
            logger.info(f"Filtrados {len(documents) - len(filtered_docs)} docs por threshold {score_threshold}")
            documents = filtered_docs
        
        # Ordenar por score descendente
        ranked_docs = sorted(
            documents, 
            key=lambda x: x.get('score', 0), 
            reverse=True
        )
        
        return ranked_docs
    
    def retrieve(self, 
                query: str, 
                k: int = 5, 
                optimize: bool = True,
                intent: str = "busqueda",
                score_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Recupera documentos relevantes del vector store.
        
        Flujo:
        1. Optimiza la query con LLM (si optimize=True)
        2. Consulta FAISS vía vectorstore_manager (implementado por Persona 2)
        3. Rankea y filtra resultados por score
        
        Args:
            query: Consulta del usuario
            k: Número de documentos a recuperar
            optimize: Si debe optimizar la query con LLM
            intent: Intención de la consulta (busqueda, resumen, comparacion, general)
            score_threshold: Umbral mínimo de similitud (None = sin filtro)
        
        Returns:
            Lista de documentos relevantes con metadata y scores
        """
        logger.info(f"Iniciando recuperación - Query: '{query[:50]}...', k={k}, intent={intent}")
        
        try:
            # Paso 1: Optimizar query si está habilitado
            if optimize:
                optimization_result = self._optimize_query(query, intent)
                search_query = optimization_result["optimized_query"]
                logger.info(f"Usando query optimizada: '{search_query[:50]}...'")
            else:
                search_query = query
                logger.info("Usando query original sin optimización")
            
            # Paso 2: Consultar vector store (implementado por Persona 2)
            # Nota: Asumimos que vectorstore_manager.similarity_search está implementado
            documents = self.vectorstore_manager.similarity_search(
                query=search_query,
                k=k,
                score_threshold=score_threshold
            )
            
            logger.info(f"Vector store retornó {len(documents)} documentos")
            
            # Paso 3: Rankear y filtrar
            ranked_docs = self._rank_and_filter(documents, score_threshold)
            
            logger.info(f"Recuperación completada: {len(ranked_docs)} documentos finales")
            return ranked_docs
            
        except Exception as e:
            logger.error(f"Error en recuperación: {str(e)}")
            return []
    
    def retrieve_for_comparison(self, query: str, num_docs: int = 4) -> List[Dict[str, Any]]:
        """
        Recupera documentos específicamente para comparaciones.
        
        Estrategia:
        - Mayor número de documentos para cubrir ambos conceptos
        - Optimización enfocada en extraer términos de ambos conceptos
        - Sin score threshold estricto (queremos diversidad)
        
        Args:
            query: Consulta de comparación (ej: "diferencia entre X e Y")
            num_docs: Número de documentos (default: 4-6 recomendado)
        
        Returns:
            Documentos relevantes para análisis comparativo
        """
        logger.info(f"Recuperación para COMPARACIÓN - Query: '{query[:50]}...', num_docs={num_docs}")
        
        # Usar retrieve estándar con parámetros optimizados para comparación
        documents = self.retrieve(
            query=query,
            k=num_docs,
            optimize=True,
            intent="comparacion",
            score_threshold=0.3  # Threshold más bajo para mayor diversidad
        )
        
        logger.info(f"Recuperados {len(documents)} documentos para comparación")
        return documents
    
    def retrieve_for_summary(self, query: str, max_docs: int = 10) -> List[Dict[str, Any]]:
        """
        Recupera documentos específicamente para resúmenes.
        
        Estrategia:
        - Mayor cantidad de documentos para cobertura amplia
        - Optimización para términos generales del dominio
        - Threshold moderado para calidad
        
        Args:
            query: Consulta de resumen (ej: "resumen de X")
            max_docs: Número máximo de documentos (default: 8-10 recomendado)
        
        Returns:
            Documentos relevantes para generación de resumen
        """
        logger.info(f"Recuperación para RESUMEN - Query: '{query[:50]}...', max_docs={max_docs}")
        
        # Usar retrieve estándar con parámetros optimizados para resumen
        documents = self.retrieve(
            query=query,
            k=max_docs,
            optimize=True,
            intent="resumen",
            score_threshold=0.4  # Threshold moderado para balance calidad/cantidad
        )
        
        logger.info(f"Recuperados {len(documents)} documentos para resumen")
        return documents
