"""
Agente Crítico Autónomo con Tools.
Valida y verifica la calidad de respuestas generadas.
"""
import logging
from typing import Dict, Any, List
from langchain.agents import create_agent
from pydantic import BaseModel, Field

from src.config.llm_config import llm_config
from src.tools import CRITIC_TOOLS

logger = logging.getLogger(__name__)


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
        Valida una respuesta de forma autónoma y rigurosa.
        
        El agente:
        1. Ejecuta validate_response para análisis completo
        2. Puede ejecutar check_hallucination si detecta problemas
        3. Analiza los resultados con criterio experto
        4. Decide si aprobar o rechazar (regenerar)
        5. Registra su decisión con razonamiento
        6. Retorna validación estructurada
        
        Args:
            query: Pregunta original del usuario
            response: Respuesta generada a validar
            context_documents: Documentos usados para generar la respuesta
            
        Returns:
            Diccionario con validación:
            {
                "is_valid": bool,  # Si la respuesta es válida
                "needs_regeneration": bool,  # Si debe regenerarse
                "confidence_score": float,  # Score 0-1
                "issues": List[str],  # Problemas encontrados
                "recommendations": str,  # Feedback para mejorar
                "reasoning": str,  # Razonamiento del agente
                "intermediate_steps": list  # Acciones ejecutadas
            }
        """
        try:
            logger.info(f"[AutonomousCritic] Validando respuesta ({len(response)} chars) vs {len(context_documents)} docs")
            
            # Preparar mensaje para el agente
            user_message = f"Query original: {query}\n\nRespuesta a validar:\n{response}\n\nNúmero de documentos de contexto: {len(context_documents)}\n\nValida la respuesta y determina si es correcta."
            
            # Ejecutar agente con formato LangChain 1.1
            result = self.agent_executor.invoke({
                "messages": [
                    {"role": "user", "content": user_message}
                ]
            })
            
            # Extraer validación del nuevo formato de mensajes
            messages = result.get("messages", [])
            output = ""
            tool_results = []
            tool_calls = []
            
            for msg in messages:
                # AIMessage con tool_calls
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tool_calls.extend(msg.tool_calls)
                # AIMessage con respuesta final
                elif hasattr(msg, 'content') and msg.content and not hasattr(msg, 'tool_call_id'):
                    output = msg.content
                # ToolMessage con resultados
                elif hasattr(msg, 'tool_call_id') and hasattr(msg, 'content'):
                    try:
                        import json
                        tool_result = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                        tool_results.append(tool_result)
                    except:
                        tool_results.append({"content": msg.content})
            
            validation_result = self._extract_validation_from_results(tool_results, output)
            
            # Agregar steps para trazabilidad
            validation_result["intermediate_steps"] = [
                {
                    "tool": tc.get("name", "unknown") if isinstance(tc, dict) else getattr(tc, 'name', 'unknown'),
                    "result_preview": str(tr)[:200] if tr else ""
                }
                for tc, tr in zip(tool_calls, tool_results + [None] * len(tool_calls))
            ]
            
            logger.info(f"[AutonomousCritic] Validación: valid={validation_result['is_valid']}, "
                       f"score={validation_result['confidence_score']:.2f}, "
                       f"regenerate={validation_result['needs_regeneration']}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"[AutonomousCritic] Error: {str(e)}")
            
            # En caso de error, ser conservador y rechazar
            return {
                "is_valid": False,
                "needs_regeneration": True,
                "confidence_score": 0.0,
                "issues": [f"Error en validación: {str(e)}"],
                "recommendations": "Revisa la respuesta manualmente",
                "reasoning": f"Error durante validación: {str(e)}",
                "intermediate_steps": []
            }
    
    def _extract_validation_from_results(self, tool_results: list, output: str) -> Dict[str, Any]:
        """
        Extrae resultado de validación de los resultados de las tools.
        
        Args:
            tool_results: Resultados de las tools ejecutadas
            output: Output final del agente
            
        Returns:
            Diccionario con validación estructurada
        """
        # Buscar resultado de validate_response en los resultados
        for result in tool_results:
            if isinstance(result, dict) and 'is_valid' in result:
                # Asegurarnos de que tiene todos los campos necesarios
                return {
                    "is_valid": result.get("is_valid", False),
                    "needs_regeneration": not result.get("is_valid", True),
                    "confidence_score": result.get("confidence_score", 0.0),
                    "issues": result.get("issues", []),
                    "recommendations": result.get("recommendations", ""),
                    "reasoning": output or "Validación completada por tool"
                }
        
        # Si no encontramos validate_response, parsear el output
        # Por defecto, ser conservador
        return {
            "is_valid": "aprobada" in output.lower() and "valid" in output.lower(),
            "needs_regeneration": "rechazada" in output.lower() or "regenera" in output.lower(),
            "confidence_score": 0.5,
            "issues": [],
            "recommendations": "Revisar validación manual",
            "reasoning": output
        }
