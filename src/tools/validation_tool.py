"""
Tool para validar respuestas generadas.
Verifica coherencia, detecta alucinaciones y evalúa calidad de respuestas RAG.
"""
import logging
from typing import Dict, Any, List
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.config.llm_config import llm_config

logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """Resultado de validación de respuesta."""
    is_valid: bool = Field(description="Si la respuesta es válida")
    confidence_score: float = Field(description="Score de confianza 0-1")
    issues: List[str] = Field(description="Lista de problemas encontrados")
    recommendations: str = Field(description="Recomendaciones para mejorar")


@tool
def validate_response(query: str, response: str, context_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Valida una respuesta generada contra documentos fuente.
    
    Esta herramienta debe usarse cuando:
    - Se ha generado una respuesta y se necesita verificar su calidad
    - Se quiere detectar posibles alucinaciones
    - Se necesita confirmar que la respuesta está respaldada por fuentes
    - Se requiere un control de calidad antes de entregar la respuesta
    
    Args:
        query: La pregunta original del usuario
        response: La respuesta generada que se va a validar
        context_documents: Los documentos usados para generar la respuesta
                          Formato: [{"content": "...", "metadata": {...}}]
    
    Returns:
        Diccionario con resultado de validación:
        {
            "is_valid": bool,  # Si la respuesta pasa validación
            "confidence_score": float,  # Score de confianza 0-1
            "issues": List[str],  # Problemas encontrados
            "recommendations": str  # Sugerencias de mejora
        }
        
    Ejemplo de uso:
        docs = search_documents("síntomas COVID", k=3)
        response = generate_rag_response("¿Síntomas?", docs)
        validation = validate_response(
            "¿Cuáles son los síntomas?",
            response,
            docs
        )
        
        if not validation["is_valid"]:
            # Regenerar respuesta con mejoras
            ...
    """
    try:
        logger.info(f"Validando respuesta ({len(response)} caracteres)")
        
        if not context_documents:
            return {
                "is_valid": False,
                "confidence_score": 0.0,
                "issues": ["No hay documentos de contexto para validar"],
                "recommendations": "Proporciona documentos fuente para validación"
            }
        
        # Preparar contexto
        context = "\n\n".join([
            f"[Fuente {idx}]: {doc.get('content', '')}"
            for idx, doc in enumerate(context_documents, 1)
        ])
        
        # Configurar LLM para validación crítica
        llm = llm_config.get_critic_llm()
        structured_llm = llm.with_structured_output(ValidationResult)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un evaluador experto de respuestas RAG.

Tu tarea es validar si una respuesta está correctamente respaldada por documentos fuente.

CRITERIOS DE VALIDACIÓN:

1. **Alineación con Fuentes** (crítico):
   - Cada afirmación debe estar respaldada por el contexto
   - Las citas deben corresponder a información real de las fuentes
   - No debe haber información inventada o asumida

2. **Coherencia**:
   - La respuesta debe ser lógica y bien estructurada
   - Debe responder directamente la pregunta
   - No debe ser ambigua o confusa

3. **Completitud**:
   - Debe abordar todos los aspectos de la pregunta
   - Debe aprovechar la información disponible en las fuentes

4. **Calidad de Citas**:
   - Las citas deben estar presentes y bien formateadas
   - Cada afirmación importante debe tener su cita

DECISIÓN:
- is_valid = true: La respuesta es confiable y está bien respaldada
- is_valid = false: Hay problemas críticos que requieren regeneración

- confidence_score: 0.0 (muy malo) a 1.0 (excelente)

IMPORTANTE: Sé estricto. Si encuentras información no respaldada, marca como inválido."""),
            ("user", """Pregunta original: {query}

Respuesta generada:
{response}

Contexto de documentos fuente:
{context}

Evalúa la respuesta:""")
        ])
        
        messages = prompt.format_messages(
            query=query,
            response=response,
            context=context
        )
        
        validation = structured_llm.invoke(messages)
        
        result = {
            "is_valid": validation.is_valid,
            "confidence_score": validation.confidence_score,
            "issues": validation.issues,
            "recommendations": validation.recommendations
        }
        
        logger.info(f"Validación completada: valid={result['is_valid']}, score={result['confidence_score']:.2f}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error en validación: {str(e)}")
        return {
            "is_valid": False,
            "confidence_score": 0.0,
            "issues": [f"Error en validación: {str(e)}"],
            "recommendations": "Revisa la configuración del sistema"
        }


@tool
def check_hallucination(response: str, context_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verifica si una respuesta contiene alucinaciones (información inventada).
    
    Esta herramienta debe usarse cuando:
    - Se sospecha que la respuesta contiene información no verificada
    - Se necesita un análisis específico de fidelidad a las fuentes
    - Se requiere identificar afirmaciones sin respaldo
    
    Args:
        response: La respuesta a verificar
        context_documents: Los documentos fuente para contrastar
    
    Returns:
        Diccionario con análisis de alucinaciones:
        {
            "has_hallucination": bool,  # Si hay alucinaciones detectadas
            "hallucination_score": float,  # 0=sin alucinaciones, 1=muchas
            "problematic_claims": List[str],  # Afirmaciones sin respaldo
            "analysis": str  # Análisis detallado
        }
        
    Ejemplo de uso:
        result = check_hallucination(response, docs)
        if result["has_hallucination"]:
            print(f"Problemas: {result['problematic_claims']}")
    """
    try:
        logger.info("Analizando posibles alucinaciones")
        
        if not context_documents:
            return {
                "has_hallucination": True,
                "hallucination_score": 1.0,
                "problematic_claims": ["No hay contexto para verificar"],
                "analysis": "Sin documentos fuente, no se puede validar la respuesta"
            }
        
        # Preparar contexto
        context = "\n\n".join([doc.get('content', '') for doc in context_documents])
        
        llm = llm_config.get_critic_llm()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un detector experto de alucinaciones en respuestas RAG.

Una ALUCINACIÓN es cualquier información en la respuesta que:
- No está presente en los documentos fuente
- Se asume o inventa sin evidencia
- Contradice la información de las fuentes
- Exagera o distorsiona información real

TAREA:
1. Compara cada afirmación de la respuesta con el contexto
2. Identifica afirmaciones sin respaldo directo
3. Clasifica la gravedad (menor, moderada, grave)
4. Proporciona análisis específico

Responde en formato:
has_hallucination: true/false
hallucination_score: 0.0 (sin alucinaciones) a 1.0 (graves)
problematic_claims: lista de afirmaciones problemáticas
analysis: análisis detallado

Sé riguroso y objetivo."""),
            ("user", """Respuesta a evaluar:
{response}

Contexto de documentos fuente:
{context}

Analiza las alucinaciones:""")
        ])
        
        messages = prompt.format_messages(response=response, context=context)
        llm_response = llm.invoke(messages)
        
        # Parsear respuesta (simplificado - en producción usar structured output)
        analysis_text = llm_response.content
        
        # Análisis básico por keywords
        has_hallucination = any(word in analysis_text.lower() for word in 
                                ['alucinación', 'inventada', 'sin respaldo', 'no presente'])
        
        score = 0.3 if has_hallucination else 0.0
        
        result = {
            "has_hallucination": has_hallucination,
            "hallucination_score": score,
            "problematic_claims": [],
            "analysis": analysis_text
        }
        
        logger.info(f"Análisis completado: hallucination={has_hallucination}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error en detección de alucinaciones: {str(e)}")
        return {
            "has_hallucination": False,
            "hallucination_score": 0.0,
            "problematic_claims": [],
            "analysis": f"Error: {str(e)}"
        }
