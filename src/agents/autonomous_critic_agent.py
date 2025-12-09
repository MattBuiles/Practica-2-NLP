"""
Agente Crítico Autónomo con Tools.
Valida y verifica la calidad de respuestas generadas.
"""
import logging
from typing import Dict, Any, List
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate

from src.config.llm_config import llm_config
from src.tools import CRITIC_TOOLS

logger = logging.getLogger(__name__)


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
        self.prompt = self._create_agent_prompt()
        
        # Crear agente con langgraph (retorna un grafo ejecutable)
        self.agent_executor = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        logger.info(f"AutonomousCriticAgent inicializado con {len(self.tools)} tools")
    
    def _create_agent_prompt(self) -> ChatPromptTemplate:
        """Crea el prompt del sistema para el agente crítico."""
        return ChatPromptTemplate.from_messages([
            ("system", """Eres un Agente Crítico Autónomo experto en validación de respuestas RAG.

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
- Explica claramente por qué apruebas o rechazas"""),
            ("placeholder", "{agent_scratchpad}"),
            ("human", """Query original: {query}

Respuesta a validar:
{response}

Número de documentos de contexto: {num_documents}

Valida la respuesta rigurosamente.""")
        ])
    
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
            
            # Preparar input
            agent_input = {
                "query": query,
                "response": response,
                "num_documents": len(context_documents),
                "input": f"Query original: {query}\n\nRespuesta a validar:\n{response}\n\nNúmero de documentos de contexto: {len(context_documents)}"
            }
            
            # Ejecutar agente
            result = self.agent_executor.invoke(agent_input)
            
            # Extraer validación de los steps
            steps = result.get("intermediate_steps", [])
            output = result.get("output", "")
            
            validation_result = self._extract_validation_from_steps(steps, output)
            
            # Agregar steps para trazabilidad
            validation_result["intermediate_steps"] = [
                {
                    "tool": step[0].tool if hasattr(step[0], 'tool') else "reasoning",
                    "result_preview": str(step[1])[:200]
                }
                for step in steps
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
    
    def _extract_validation_from_steps(self, steps: list, output: str) -> Dict[str, Any]:
        """
        Extrae resultado de validación de los steps del agente.
        
        Args:
            steps: Pasos intermedios ejecutados
            output: Output final del agente
            
        Returns:
            Diccionario con validación estructurada
        """
        # Buscar resultado de validate_response en los steps
        for step in steps:
            if hasattr(step[0], 'tool') and step[0].tool == 'validate_response':
                result = step[1]
                if isinstance(result, dict):
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
