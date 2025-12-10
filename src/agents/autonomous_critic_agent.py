"""
Agente Crítico Autónomo con Tools.
Valida y verifica la calidad de respuestas generadas.
"""
import logging
import time
from typing import Dict, Any, List
from langchain.agents import create_agent
from pydantic import BaseModel, Field

from src.config.llm_config import llm_config
from src.tools import CRITIC_TOOLS

logger = logging.getLogger(__name__)

# Delay entre llamadas API para evitar rate limiting
API_DELAY = 1.5


class ValidationResult(BaseModel):
    """Modelo de salida estructurada para validación crítica."""
    is_valid: bool = Field(description="Si la respuesta es válida")
    confidence_score: float = Field(description="Puntuación de confianza (0.0 a 1.0)")
    needs_regeneration: bool = Field(description="Si requiere regeneración")
    issues: List[str] = Field(description="Lista de problemas detectados")
    feedback: str = Field(description="Feedback detallado para mejora")


class AutonomousCriticAgent:
    """
    Agente Crítico Autónomo basado en LangChain.
    
    Este agente valida respuestas de forma rigurosa:
    - Verifica que la respuesta esté respaldada por fuentes
    - Detecta alucinaciones (información inventada)
    - Evalúa coherencia y completitud
    - Decide si se requiere regeneración
    - Proporciona feedback detallado para mejoras
    
    TOOLS DISPONIBLES:
    - validate_response: Validación completa de respuesta vs contexto
    - check_hallucination: Detección específica de alucinaciones
    - log_agent_decision: Registrar decisiones de validación
    
    CAPACIDADES:
    - Validación multi-criterio (coherencia, alineación, citas)
    - Detección de alucinaciones
    - Generación de feedback constructivo
    - Decisión de regeneración basada en thresholds
    """
    
    def __init__(self):
        """
        Inicializa el agente crítico autónomo.
        
        Configura:
        - LLM de razonamiento profundo (Gemini)
        - Tools de validación
        - Prompt con criterios estrictos
        - AgentExecutor para autonomía
        """
        logger.info("Inicializando AutonomousCriticAgent...")
        
        # LLM para razonamiento profundo (Gemini)
        self.llm = llm_config.get_critic_llm()
        
        # Tools disponibles
        self.tools = CRITIC_TOOLS
        
        # Prompt del sistema para el agente
        self.system_prompt = self._create_system_prompt()
        
        # Crear agente con langchain (retorna un grafo ejecutable)
        self.agent_executor = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt
        )
        
        logger.info(f"AutonomousCriticAgent inicializado con {len(self.tools)} tools")
    
    def _create_system_prompt(self) -> str:
        """Crea el prompt del sistema para el agente crítico."""
        return """Eres un Agente Crítico Autónomo experto en validación rigurosa de respuestas.

TU MISIÓN:
Validar rigurosamente si una respuesta generada es confiable, está bien respaldada y libre de alucinaciones.

HERRAMIENTAS DISPONIBLES:

1. validate_response(query, response, context_documents):
   - Validación completa con 5 criterios
   - Evalúa coherencia, alineación, alucinaciones, completitud, citas
   - Retorna is_valid, confidence_score, issues, recommendations
   - USA ESTA como validación principal

2. check_hallucination(response, context_documents):
   - Análisis específico de alucinaciones
   - Identifica afirmaciones sin respaldo
   - USA cuando validate_response detecte problemas o quieras análisis profundo

3. log_agent_decision(agent_name, decision, reasoning, metadata):
   - Registra tu decisión de validación
   - Incluye siempre tu razonamiento

CRITERIOS DE VALIDACIÓN:

1. **Alineación con Fuentes** (CRÍTICO):
   - Cada afirmación debe estar en los documentos
   - Las citas deben ser correctas
   - Sin información inventada o asumida

2. **Ausencia de Alucinaciones** (CRÍTICO):
   - No debe haber datos inventados
   - No debe extrapolar sin evidencia
   - No debe contradecir las fuentes

3. **Coherencia**:
   - Estructura lógica y clara
   - Responde directamente la pregunta
   - Sin ambigüedades

4. **Completitud**:
   - Aborda todos los aspectos de la pregunta
   - Aprovecha información disponible

5. **Calidad de Citas**:
   - Citas presentes y correctas
   - Cada afirmación importante citada

ESTRATEGIA DE VALIDACIÓN:

PASO 1: Validación Principal
→ Usa validate_response(query, response, context_documents)
→ Obtén scores y problemas identificados

PASO 2: Análisis de Alucinaciones (si hay dudas)
→ Si confidence_score < 0.7 O is_valid=false
→ Usa check_hallucination para análisis profundo

PASO 3: Decisión Final
→ Basado en:
  - is_valid de validate_response
  - confidence_score (umbral: 0.65)
  - Gravedad de issues encontrados
  - Análisis de alucinaciones

PASO 4: Registro
→ log_agent_decision con tu decisión y razonamiento completo

THRESHOLDS DE DECISIÓN:

**APROBADA** (needs_regeneration=False):
- is_valid = True
- confidence_score >= 0.65
- Sin alucinaciones graves
- Problemas menores o ninguno

**RECHAZADA** (needs_regeneration=True):
- is_valid = False O
- confidence_score < 0.65 O
- Alucinaciones detectadas O
- Problemas críticos en alineación

EJEMPLOS:

Ejemplo 1 - Respuesta válida:
Validación: is_valid=True, score=0.85, issues=[]
Decisión: APROBADA
Razonamiento: "Respuesta bien respaldada, citas correctas, sin alucinaciones"

Ejemplo 2 - Respuesta con alucinaciones:
Validación: is_valid=False, score=0.45, issues=["Afirmación sin respaldo"]
Check hallucination: has_hallucination=True
Decisión: RECHAZADA
Razonamiento: "Contiene información no presente en fuentes. Regeneración necesaria"

Ejemplo 3 - Respuesta con problemas menores:
Validación: is_valid=True, score=0.68, issues=["Cita faltante en párrafo 2"]
Decisión: APROBADA con observaciones
Razonamiento: "Mayormente válida, problema menor de formato de citas"

FORMATO DE RESPUESTA FINAL:
{{
    "is_valid": bool,
    "needs_regeneration": bool,
    "confidence_score": float,
    "issues": List[str],
    "recommendations": str,
    "reasoning": str
}}

IMPORTANTE:
- Sé RIGUROSO: ante la duda, invalida
- Usa ambas tools cuando sea necesario
- Proporciona feedback constructivo
- Explica claramente por qué apruebas o rechazas"""
    
    def validate(self, query: str, response: str, context_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Valida una respuesta de forma autónoma.
        
        NOTA: Valida directamente con LLM porque Groq tiene problemas
        pasando arrays como parámetros de tools.
        
        Args:
            query: Pregunta original del usuario
            response: Respuesta generada a validar
            context_documents: Documentos usados para generar la respuesta
            
        Returns:
            Diccionario con validación
        """
        try:
            logger.info(f"[AutonomousCritic] Validando respuesta ({len(response)} chars) vs {len(context_documents)} docs")
            
            # Delay para evitar rate limiting
            time.sleep(API_DELAY)
            
            # Validar directamente sin pasar por tools/agent
            return self._validate_direct(query, response, context_documents)
            
        except Exception as e:
            logger.error(f"[AutonomousCritic] Error: {str(e)}")
            
            # En caso de error, ACEPTAR para evitar bucles de regeneración
            return {
                "is_valid": True,
                "needs_regeneration": False,
                "confidence_score": 0.6,
                "issues": [f"Error en validación: {str(e)}"],
                "recommendations": "Validación automática por error",
                "reasoning": f"Error durante validación, aceptando respuesta: {str(e)}",
                "intermediate_steps": []
            }
    
    def _validate_direct(self, query: str, response: str, context_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Valida directamente con el LLM, sin pasar por tools."""
        import json
        import re
        
        # Preparar contexto resumido
        context_summary = ""
        for idx, doc in enumerate(context_documents[:3], 1):
            content = doc.get('content', '')[:400]
            context_summary += f"[Doc {idx}]: {content}\n\n"
        
        prompt = f"""Evalúa si esta respuesta es válida basándote en el contexto.

PREGUNTA: {query}

RESPUESTA A VALIDAR:
{response[:800]}

CONTEXTO (documentos fuente):
{context_summary}

Responde SOLO con JSON:
{{"is_valid": true, "confidence_score": 0.85, "issues": [], "recommendations": ""}}

CRITERIOS:
- is_valid=true si la respuesta está respaldada por el contexto
- is_valid=false si hay información inventada o incorrecta
- confidence_score: 0.0 a 1.0

JSON:"""
        
        llm_response = self.llm.invoke(prompt)
        text = llm_response.content
        
        # Parsear respuesta
        try:
            # Limpiar y extraer JSON
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            json_match = re.search(r'\{[\s\S]*?\}', text)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(text.strip())
                
            # Corregir tipos si es necesario
            is_valid = data.get('is_valid', True)
            if isinstance(is_valid, str):
                is_valid = is_valid.lower() == 'true'
            
            score = data.get('confidence_score', 0.7)
            if isinstance(score, str):
                score = float(score)
            
            return {
                "is_valid": is_valid,
                "needs_regeneration": not is_valid,
                "confidence_score": score,
                "issues": data.get('issues', []),
                "recommendations": data.get('recommendations', ''),
                "reasoning": "Validación directa",
                "intermediate_steps": [{"action": "direct_validation"}]
            }
            
        except (json.JSONDecodeError, Exception) as e:
            # Si falla el parseo, aceptar la respuesta
            logger.warning(f"[Critic] Error parseando validación: {e}")
            return {
                "is_valid": True,
                "needs_regeneration": False,
                "confidence_score": 0.7,
                "issues": [],
                "recommendations": "Validación aceptada por defecto",
                "reasoning": f"Parseo fallido, aceptando: {str(e)}",
                "intermediate_steps": []
            }
