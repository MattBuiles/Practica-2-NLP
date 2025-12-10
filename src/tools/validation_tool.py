"""
Tool para validar respuestas generadas.
Verifica coherencia, detecta alucinaciones y evalúa calidad de respuestas RAG.
"""
import logging
import json
import re
import time
from typing import Dict, Any, List
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.config.llm_config import llm_config

logger = logging.getLogger(__name__)

# Delay entre llamadas API
API_DELAY = 1.0


def _parse_validation_json(text: str) -> Dict[str, Any]:
    """Parsea respuesta JSON de validación, corrigiendo tipos si es necesario."""
    # Limpiar markdown
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()
    
    # Buscar JSON en el texto
    json_match = re.search(r'\{[\s\S]*?\}', text)
    if json_match:
        text = json_match.group()
    
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Limpiar newlines y reintentar
        cleaned = re.sub(r'\n\s*', ' ', text)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Extraer campos manualmente
            valid_match = re.search(r'"is_valid"\s*:\s*(true|false)', text, re.I)
            score_match = re.search(r'"confidence_score"\s*:\s*([\d.]+)', text)
            
            return {
                "is_valid": valid_match.group(1).lower() == 'true' if valid_match else True,
                "confidence_score": float(score_match.group(1)) if score_match else 0.7,
                "issues": [],
                "recommendations": "Validación completada"
            }
    
    # Corregir tipos
    if 'is_valid' in data and isinstance(data['is_valid'], str):
        data['is_valid'] = data['is_valid'].lower() == 'true'
    if 'confidence_score' in data and isinstance(data['confidence_score'], str):
        data['confidence_score'] = float(data['confidence_score'])
    if 'issues' not in data:
        data['issues'] = []
    if 'recommendations' not in data:
        data['recommendations'] = ""
        
    return data


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
        
        # Configurar LLM para validación crítica (SIN structured_output)
        llm = llm_config.get_critic_llm()
        # NO usar structured_output - Groq devuelve strings incorrectos
        
        # Delay para evitar rate limiting
        time.sleep(API_DELAY)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un evaluador experto de respuestas RAG.

Tu tarea es validar si una respuesta está correctamente respaldada por documentos fuente.

RESPONDE ÚNICAMENTE CON JSON VÁLIDO (sin markdown, sin explicaciones):

{
  "is_valid": true,
  "confidence_score": 0.85,
  "issues": [],
  "recommendations": "La respuesta es correcta"
}

CRITERIOS DE VALIDACIÓN:
1. Alineación con Fuentes: cada afirmación debe estar en los documentos
2. Coherencia: respuesta lógica y directa
3. Completitud: aborda todos los aspectos
4. Calidad de Citas: citas presentes y correctas

VALORES:
- is_valid: true/false (booleano)
- confidence_score: 0.0 a 1.0 (número)
- issues: lista de strings con problemas
- recommendations: string con sugerencias

SOLO RESPONDE CON EL JSON."""),
            ("user", """Pregunta: {query}

Respuesta a validar:
{response}

Fuentes:
{context}

Evalúa (responde SOLO con JSON):""")
        ])
        
        messages = prompt.format_messages(
            query=query,
            response=response,
            context=context[:3000]  # Limitar contexto para evitar tokens excesivos
        )
        
        llm_response = llm.invoke(messages)
        validation = _parse_validation_json(llm_response.content)
        
        result = {
            "is_valid": validation.get("is_valid", False),
            "confidence_score": float(validation.get("confidence_score", 0.5)),
            "issues": validation.get("issues", []),
            "recommendations": validation.get("recommendations", "")
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
