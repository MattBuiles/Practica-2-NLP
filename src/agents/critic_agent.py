"""
Agente Crítico/Verificador.
Implementación: Persona 3

Responsabilidades:
- Validar coherencia estructural de respuestas
- Detectar alucinaciones (información no presente en contexto)
- Verificar alineación con documentos fuente
- Evaluar completitud y calidad de citas
- Decidir si regenerar respuesta (ciclo de realimentación)
"""
import logging
from typing import Dict, Any, List, Callable, Optional
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.config.llm_config import llm_config

logger = logging.getLogger(__name__)


class ValidationCriteria(BaseModel):
    """Modelo para criterios de validación estructurados."""
    coherence_score: float = Field(description="Score de coherencia estructural (0-1)")
    alignment_score: float = Field(description="Score de alineación con contexto (0-1)")
    hallucination_score: float = Field(description="Score libre de alucinaciones (0-1, 1=sin alucinaciones)")
    completeness_score: float = Field(description="Score de completitud de respuesta (0-1)")
    citation_score: float = Field(description="Score de calidad de citas (0-1)")
    
    coherence_reasoning: str = Field(description="Justificación del score de coherencia")
    alignment_reasoning: str = Field(description="Justificación del score de alineación")
    hallucination_reasoning: str = Field(description="Justificación del score de alucinaciones")
    completeness_reasoning: str = Field(description="Justificación del score de completitud")
    citation_reasoning: str = Field(description="Justificación del score de citas")
    
    overall_assessment: str = Field(description="Evaluación general de la respuesta")
    needs_regeneration: bool = Field(description="Si la respuesta debe regenerarse")
    specific_issues: List[str] = Field(description="Lista de problemas específicos encontrados")


class CriticAgent:
    """
    Agente Crítico/Verificador.
    
    Estrategia de validación:
    1. Evalúa 5 criterios independientes con scores 0-1
    2. Cada criterio tiene justificación detallada
    3. Calcula score ponderado global
    4. Decide regeneración basado en thresholds y problemas críticos
    5. Proporciona feedback detallado para mejora
    
    Criterios de evaluación:
    - Coherencia (20%): Estructura lógica y fluidez
    - Alineación (30%): Fidelidad al contexto proporcionado
    - Alucinaciones (25%): Ausencia de información inventada
    - Completitud (15%): Responde completamente la pregunta
    - Citas (10%): Calidad y presencia de referencias
    
    Usa Gemini 2.5 Flash por su capacidad de razonamiento profundo.
    """
    
    def __init__(self):
        """Inicializa el agente crítico con LLM y configuración de validación."""
        logger.info("Inicializando CriticAgent...")
        
        # LLM para validación (Gemini - razonamiento profundo)
        self.llm = llm_config.get_critic_llm()
        self.structured_llm = self.llm.with_structured_output(ValidationCriteria)
        
        # Prompt de validación
        self.validation_prompt = self._create_validation_prompt()
        
        # Pesos para score ponderado
        self.weights = {
            'coherence': 0.20,
            'alignment': 0.30,
            'hallucination': 0.25,
            'completeness': 0.15,
            'citation': 0.10
        }
        
        # Thresholds para decisión de regeneración
        self.min_overall_score = 0.65  # Score mínimo aceptable
        self.min_hallucination_score = 0.70  # Threshold crítico para alucinaciones
        self.min_alignment_score = 0.60  # Threshold crítico para alineación
        
        logger.info("CriticAgent inicializado con Gemini 2.5 Flash")
    
    def _create_validation_prompt(self) -> ChatPromptTemplate:
        """
        Crea el prompt para validación exhaustiva de respuestas.
        
        El prompt instruye al LLM a evaluar cada criterio independientemente
        con justificación detallada.
        """
        return ChatPromptTemplate.from_messages([
            ("system", """Eres un evaluador experto de respuestas RAG. Tu tarea es validar respuestas generadas por sistemas de IA de forma rigurosa y objetiva.

CRITERIOS DE EVALUACIÓN (cada uno con score 0-1):

1. **COHERENCIA** (0-1): Evalúa la estructura lógica y fluidez
   - ¿La respuesta está bien organizada?
   - ¿Las ideas fluyen de forma lógica?
   - ¿Es fácil de entender?
   Penaliza: Incoherencias, saltos lógicos, redundancias

2. **ALINEACIÓN** (0-1): Evalúa fidelidad al contexto proporcionado
   - ¿Cada afirmación está respaldada por el contexto?
   - ¿Se usa correctamente la información del contexto?
   - ¿Se mantiene fiel a los documentos fuente?
   Penaliza: Interpretaciones incorrectas, distorsión de información

3. **ALUCINACIONES** (0-1): Detecta información inventada
   - 1.0 = Sin alucinaciones (toda la info está en el contexto)
   - 0.5 = Algunas inferencias no respaldadas
   - 0.0 = Información inventada o falsa
   CRÍTICO: Cualquier afirmación no presente en el contexto es alucinación

4. **COMPLETITUD** (0-1): Evalúa si responde completamente
   - ¿Se responde la pregunta del usuario?
   - ¿Se cubren todos los aspectos solicitados?
   - ¿La respuesta es suficientemente detallada?
   Penaliza: Respuestas parciales, omisión de información relevante

5. **CITAS** (0-1): Evalúa calidad de referencias
   - ¿Están presentes las citas [Fuente X]?
   - ¿Las citas son apropiadas y precisas?
   - ¿Cada afirmación importante tiene su cita?
   Penaliza: Ausencia de citas, citas incorrectas

DECISIÓN DE REGENERACIÓN:
Marca needs_regeneration=True si:
- Score de alucinaciones < 0.7 (problema crítico)
- Score de alineación < 0.6 (problema crítico)
- Score global < 0.65
- Hay problemas graves listados en specific_issues

FORMATO DE SALIDA:
Proporciona scores numéricos (0-1) y justificaciones detalladas para cada criterio.
Lista problemas específicos encontrados.
Proporciona evaluación general y decisión de regeneración."""),
            ("human", """Contexto de documentos fuente:
{context}

Pregunta del usuario:
{query}

Respuesta generada a evaluar:
{response}

Evalúa la respuesta de forma rigurosa y objetiva."""),
        ])
    
    def _format_context_for_validation(self, context_docs: List[Dict[str, Any]]) -> str:
        """
        Formatea los documentos de contexto para validación.
        
        Args:
            context_docs: Documentos usados para generar la respuesta
        
        Returns:
            String formateado con todos los documentos
        """
        if not context_docs:
            return "No se proporcionó contexto."
        
        context_parts = []
        for idx, doc in enumerate(context_docs, 1):
            content = doc.get('content', doc.get('page_content', ''))
            metadata = doc.get('metadata', {})
            source = metadata.get('source', 'Desconocida')
            
            context_parts.append(
                f"[Fuente {idx}] ({source})\n{content}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def _calculate_overall_score(self, validation: ValidationCriteria) -> float:
        """
        Calcula el score ponderado global basado en los 5 criterios.
        
        Args:
            validation: Criterios de validación con scores individuales
        
        Returns:
            Score global ponderado (0-1)
        """
        overall = (
            validation.coherence_score * self.weights['coherence'] +
            validation.alignment_score * self.weights['alignment'] +
            validation.hallucination_score * self.weights['hallucination'] +
            validation.completeness_score * self.weights['completeness'] +
            validation.citation_score * self.weights['citation']
        )
        
        return round(overall, 3)
    
    def validate(self, 
                query: str, 
                response: str, 
                context_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Valida una respuesta generada contra el contexto fuente.
        
        Flujo:
        1. Formatea contexto para el LLM validador
        2. Invoca Gemini para evaluar los 5 criterios
        3. Calcula score global ponderado
        4. Decide si requiere regeneración
        5. Retorna validación estructurada con feedback
        
        Args:
            query: Pregunta original del usuario
            response: Respuesta generada por RAGAgent
            context_docs: Documentos usados para generar la respuesta
        
        Returns:
            Diccionario con validación completa:
            - is_valid: Si la respuesta es aceptable
            - overall_score: Score global ponderado
            - needs_regeneration: Si debe regenerarse
            - criteria_scores: Scores individuales de cada criterio
            - feedback: Justificaciones y problemas encontrados
            - issues: Lista de problemas específicos
        """
        logger.info(f"Validando respuesta - Query: '{query[:50]}...', Response length: {len(response)} chars")
        
        try:
            # Paso 1: Formatear contexto
            context = self._format_context_for_validation(context_docs)
            
            # Paso 2: Invocar LLM validador
            messages = self.validation_prompt.format_messages(
                context=context,
                query=query,
                response=response
            )
            
            validation = self.structured_llm.invoke(messages)
            
            # Paso 3: Calcular score global
            overall_score = self._calculate_overall_score(validation)
            
            # Paso 4: Verificar decisión de regeneración con thresholds
            # Combinar la decisión del LLM con thresholds de seguridad
            needs_regen = (
                validation.needs_regeneration or
                overall_score < self.min_overall_score or
                validation.hallucination_score < self.min_hallucination_score or
                validation.alignment_score < self.min_alignment_score
            )
            
            # Construir resultado estructurado
            result = {
                "is_valid": not needs_regen,
                "overall_score": overall_score,
                "needs_regeneration": needs_regen,
                "criteria_scores": {
                    "coherence": validation.coherence_score,
                    "alignment": validation.alignment_score,
                    "hallucination": validation.hallucination_score,
                    "completeness": validation.completeness_score,
                    "citation": validation.citation_score
                },
                "feedback": {
                    "coherence": validation.coherence_reasoning,
                    "alignment": validation.alignment_reasoning,
                    "hallucination": validation.hallucination_reasoning,
                    "completeness": validation.completeness_reasoning,
                    "citation": validation.citation_reasoning,
                    "overall": validation.overall_assessment
                },
                "issues": validation.specific_issues,
                "weights_used": self.weights
            }
            
            logger.info(f"Validación completada - Score: {overall_score:.3f}, Valid: {result['is_valid']}")
            
            if needs_regen:
                logger.warning(f"Respuesta requiere regeneración - Issues: {len(validation.specific_issues)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error en validación: {str(e)}")
            # En caso de error, asumir válida para no bloquear el sistema
            return {
                "is_valid": True,
                "overall_score": 0.5,
                "needs_regeneration": False,
                "criteria_scores": {},
                "feedback": {"error": f"Error en validación: {str(e)}"},
                "issues": [f"Error en validación: {str(e)}"],
                "error": str(e)
            }
    
    def validate_with_regeneration(self, 
                                   query: str, 
                                   response: str,
                                   context_docs: List[Dict[str, Any]],
                                   regenerate_callback: Callable[[str, List[Dict[str, Any]], str], Dict[str, Any]],
                                   max_attempts: int = 2) -> Dict[str, Any]:
        """
        Valida con ciclo de realimentación y regeneración automática.
        
        Flujo:
        1. Valida la respuesta inicial
        2. Si needs_regeneration=True y quedan intentos:
           a. Invoca callback para regenerar
           b. Valida la nueva respuesta
           c. Repite hasta max_attempts o respuesta válida
        3. Retorna mejor respuesta obtenida con historial completo
        
        Args:
            query: Pregunta original del usuario
            response: Respuesta inicial generada
            context_docs: Documentos de contexto
            regenerate_callback: Función para regenerar respuesta
                                Firma: (query, context_docs, intent) -> Dict[str, Any]
            max_attempts: Máximo número de intentos (default: 2)
        
        Returns:
            Diccionario con:
            - final_response: Mejor respuesta obtenida
            - validation: Validación de la respuesta final
            - attempts: Número de intentos realizados
            - status: Estado final (validated, regenerated, max_attempts_reached)
            - history: Historial de todas las validaciones
        """
        logger.info(f"Iniciando validación con regeneración - Max attempts: {max_attempts}")
        
        history = []
        current_response = response
        attempt = 1
        
        while attempt <= max_attempts:
            logger.info(f"Intento {attempt}/{max_attempts} - Validando respuesta...")
            
            # Validar respuesta actual
            validation = self.validate(query, current_response, context_docs)
            
            # Guardar en historial
            history.append({
                "attempt": attempt,
                "response": current_response,
                "validation": validation
            })
            
            # Si la respuesta es válida, terminar
            if not validation["needs_regeneration"]:
                logger.info(f"Respuesta VÁLIDA en intento {attempt} - Score: {validation['overall_score']:.3f}")
                return {
                    "final_response": current_response,
                    "validation": validation,
                    "attempts": attempt,
                    "status": "validated" if attempt == 1 else "regenerated",
                    "history": history
                }
            
            # Si quedan intentos, regenerar
            if attempt < max_attempts:
                logger.warning(f"Respuesta requiere regeneración - Intento {attempt}/{max_attempts}")
                logger.info(f"Problemas encontrados: {validation['issues']}")
                
                try:
                    # Invocar callback de regeneración
                    # Nota: El callback debe ser RAGAgent.generate_response
                    logger.info("Invocando callback de regeneración...")
                    regenerated = regenerate_callback(query, context_docs, "busqueda")
                    current_response = regenerated.get("response", current_response)
                    logger.info(f"Nueva respuesta generada - Length: {len(current_response)} chars")
                    
                except Exception as e:
                    logger.error(f"Error en regeneración: {str(e)}")
                    # Si falla la regeneración, mantener respuesta actual
                    break
            
            attempt += 1
        
        # Si se alcanzó max_attempts sin respuesta válida
        logger.warning(f"Max attempts ({max_attempts}) alcanzados sin validación exitosa")
        
        # Seleccionar la mejor respuesta del historial (mayor score)
        best_entry = max(history, key=lambda x: x["validation"]["overall_score"])
        
        logger.info(f"Usando mejor respuesta - Attempt {best_entry['attempt']}, Score: {best_entry['validation']['overall_score']:.3f}")
        
        return {
            "final_response": best_entry["response"],
            "validation": best_entry["validation"],
            "attempts": max_attempts,
            "status": "max_attempts_reached",
            "history": history,
            "best_attempt": best_entry["attempt"]
        }
