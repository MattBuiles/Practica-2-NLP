"""
Agente Clasificador Autónomo con Tools.
Usa LangChain agent con capacidad de usar herramientas de forma autónoma.
"""
import logging
import time
from typing import Dict, Any
from langchain.agents import create_agent
from pydantic import BaseModel, Field

from src.config.llm_config import llm_config
from src.tools import CLASSIFIER_TOOLS, classify_intent, log_agent_decision

logger = logging.getLogger(__name__)

# Delay entre llamadas API para evitar rate limiting
API_DELAY = 1.5


class IntentClassification(BaseModel):
    """Modelo de salida estructurada para clasificación de intención."""
    intent: str = Field(description="Intención clasificada: busqueda, resumen, comparacion, general")
    confidence: float = Field(description="Nivel de confianza (0.0 a 1.0)")
    requires_rag: bool = Field(description="Si requiere búsqueda en vector store")
    reasoning: str = Field(description="Justificación de la clasificación")


class AutonomousClassifierAgent:
    """
    Agente Clasificador Autónomo basado en LangChain.
    
    Este agente es verdaderamente autónomo:
    - Decide cuándo usar las tools disponibles
    - Puede clasificar directamente o usar la tool classify_intent
    - Registra sus decisiones automáticamente
    - Razona sobre la mejor estrategia para cada consulta
    
    TOOLS DISPONIBLES:
    - classify_intent: Clasificar intención usando LLM
    - get_available_documents_info: Ver documentos disponibles
    - log_agent_decision: Registrar decisiones
    
    CAPACIDADES:
    - Clasificación de intención (busqueda, resumen, comparacion, general)
    - Determinación de necesidad de RAG
    - Análisis contextual profundo
    - Trazabilidad automática
    """
    
    def __init__(self):
        """
        Inicializa el agente clasificador autónomo.
        
        Configura:
        - LLM con capacidad de tool calling (Gemini 2.5 Flash)
        - Tools específicas para clasificación
        - Prompt con instrucciones detalladas
        - AgentExecutor para ejecución autónoma
        """
        logger.info("Inicializando AutonomousClassifierAgent...")
        
        # LLM con tool calling (Gemini - comprensión contextual)
        self.llm = llm_config.get_classifier_llm()
        
        # Tools disponibles para este agente
        self.tools = CLASSIFIER_TOOLS
        
        # Prompt del sistema para el agente
        self.system_prompt = self._create_system_prompt()
        
        # Crear agente con langchain (retorna un grafo ejecutable)
        self.agent_executor = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt
        )
        
        logger.info(f"AutonomousClassifierAgent inicializado con {len(self.tools)} tools")
    
    def _create_system_prompt(self) -> str:
        """
        Crea el prompt del sistema para el agente autónomo.
        
        El prompt debe:
        - Explicar claramente la tarea del agente
        - Describir cuándo usar cada tool
        - Proporcionar ejemplos de razonamiento
        - Establecer el formato de salida esperado
        """
        return """Eres un Agente Clasificador Autónomo experto en análisis de intenciones.

TU MISIÓN:
Clasificar la intención del usuario en una de 4 categorías:
1. **busqueda**: Usuario busca información específica en documentos
2. **resumen**: Usuario quiere un resumen de documentos
3. **comparacion**: Usuario quiere comparar conceptos/documentos
4. **general**: Conversación general sin necesidad de documentos

HERRAMIENTAS DISPONIBLES:
- classify_intent: Usa esta tool para clasificar la intención usando LLM especializado
- get_available_documents_info: Consulta qué documentos están disponibles
- log_agent_decision: Registra tu decisión para trazabilidad

ESTRATEGIA DE DECISIÓN:

1. **Analiza la consulta cuidadosamente**:
   - ¿Busca información específica? → busqueda
   - ¿Pide resumen explícitamente? → resumen
   - ¿Compara dos conceptos? → comparacion
   - ¿Es conversacional? → general

2. **Usa classify_intent cuando**:
   - La consulta es ambigua o compleja
   - Necesitas análisis profundo del lenguaje
   - Quieres una segunda opinión

3. **Verifica documentos disponibles cuando**:
   - El usuario pregunta sobre la disponibilidad de información
   - Necesitas confirmar si hay contenido relevante

4. **Registra tu decisión siempre**:
   - Usa log_agent_decision para trazabilidad
   - Incluye tu razonamiento completo

EJEMPLOS DE RAZONAMIENTO:

Ejemplo 1:
Query: "¿Qué es la diabetes?"
Razonamiento: "Es una pregunta directa sobre un concepto específico. 
El usuario busca definición e información. Clasifico como 'busqueda' 
con requires_rag=True."

Ejemplo 2:
Query: "Resume el artículo sobre COVID"
Razonamiento: "El usuario solicita explícitamente un resumen. 
Clasifico como 'resumen' con requires_rag=True."

Ejemplo 3:
Query: "Hola, ¿cómo estás?"
Razonamiento: "Es un saludo conversacional sin intención de buscar información. 
Clasifico como 'general' con requires_rag=False."

FORMATO DE RESPUESTA FINAL:
Debes devolver un diccionario con:
{{
    "intent": "busqueda|resumen|comparacion|general",
    "confidence": 0.0-1.0,
    "requires_rag": true|false,
    "reasoning": "Tu razonamiento detallado"
}}

IMPORTANTE:
- Sé preciso y confiable
- Explica claramente tu razonamiento
- Usa las tools cuando sea apropiado
- No inventes información"""
    
    def classify(self, query: str) -> Dict[str, Any]:
        """
        Clasifica la intención de una consulta de forma autónoma.
        
        El agente:
        1. Analiza la consulta
        2. Decide si usar tools o razonar directamente
        3. Usa classify_intent si necesita análisis profundo
        4. Registra su decisión con log_agent_decision
        5. Retorna clasificación con razonamiento
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Diccionario con clasificación:
            {
                "intent": str,
                "confidence": float,
                "requires_rag": bool,
                "reasoning": str,
                "intermediate_steps": list  # Pasos del agente
            }
        """
        try:
            logger.info(f"[AutonomousClassifier] Procesando: '{query[:100]}'")
            
            # Delay para evitar rate limiting
            time.sleep(API_DELAY)
            
            # Invocar agente autónomo con formato LangChain 1.1
            # El nuevo formato usa 'messages' como lista de mensajes
            result = self.agent_executor.invoke({
                "messages": [
                    {"role": "user", "content": f"Clasifica la siguiente consulta del usuario: {query}"}
                ]
            })
            
            # Extraer resultado del nuevo formato (messages es una lista)
            messages = result.get("messages", [])
            
            # Procesar los mensajes para extraer información
            output = ""
            tool_calls = []
            tool_results = []
            
            for msg in messages:
                # AIMessage con respuesta final
                if hasattr(msg, 'content') and msg.content and not hasattr(msg, 'tool_call_id'):
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        tool_calls.extend(msg.tool_calls)
                    elif msg.content:
                        output = msg.content
                # ToolMessage con resultados
                elif hasattr(msg, 'tool_call_id'):
                    try:
                        import json
                        tool_result = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                        tool_results.append(tool_result)
                    except:
                        tool_results.append({"content": msg.content})
            
            logger.info(f"[AutonomousClassifier] Tool calls: {len(tool_calls)}, Tool results: {len(tool_results)}")
            
            # Parsear output
            classification = self._parse_agent_output(output, tool_results)
            
            # Agregar pasos intermedios para trazabilidad
            classification["intermediate_steps"] = [
                {
                    "action": tc.get("name", "unknown") if isinstance(tc, dict) else getattr(tc, 'name', 'unknown'),
                    "input": str(tc.get("args", {}) if isinstance(tc, dict) else getattr(tc, 'args', {}))[:200],
                    "output": str(tr)[:200] if tr else ""
                }
                for tc, tr in zip(tool_calls, tool_results + [None] * len(tool_calls))
            ]
            
            logger.info(f"[AutonomousClassifier] Clasificado como: {classification['intent']}")
            
            return classification
            
        except Exception as e:
            logger.error(f"[AutonomousClassifier] Error: {str(e)}")
            # Fallback seguro
            return {
                "intent": "busqueda",
                "confidence": 0.5,
                "requires_rag": True,
                "reasoning": f"Error en clasificación autónoma: {str(e)}",
                "intermediate_steps": []
            }
    
    def _parse_agent_output(self, output: str, tool_results: list) -> Dict[str, Any]:
        """
        Parsea la salida del agente para extraer clasificación estructurada.
        
        Args:
            output: Salida final del agente
            tool_results: Resultados de las tools ejecutadas
            
        Returns:
            Diccionario con clasificación estructurada
        """
        # Buscar si hay resultados de classify_intent en tool_results
        for result in tool_results:
            if isinstance(result, dict) and 'intent' in result:
                return result
        
        # Si no se usó classify_intent, parsear el output del agente
        # Buscar palabras clave en el output
        output_lower = output.lower()
        
        intent = "busqueda"  # default
        if "resumen" in output_lower:
            intent = "resumen"
        elif "comparacion" in output_lower or "comparar" in output_lower:
            intent = "comparacion"
        elif "general" in output_lower or "conversacion" in output_lower:
            intent = "general"
        
        requires_rag = intent != "general"
        
        return {
            "intent": intent,
            "confidence": 0.75,  # Confianza media si no usó classify_intent
            "requires_rag": requires_rag,
            "reasoning": output
        }
