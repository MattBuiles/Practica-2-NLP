"""
Agente de Generación de Respuestas RAG.
Implementación: Persona 3

Responsabilidades:
- Generar respuestas basadas en contexto recuperado usando LLM
- Incluir citas de fuentes en las respuestas
- Adaptar estilo y formato según intención (búsqueda, resumen, comparación)
- Manejar respuestas generales sin RAG para consultas conversacionales
"""
import logging
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate

from src.config.llm_config import llm_config

logger = logging.getLogger(__name__)


class RAGAgent:
    """
    Agente de Generación de Respuestas RAG.
    
    Estrategia:
    1. Prompts especializados según intención:
       - Búsqueda: Respuestas precisas y concisas con citas explícitas
       - Resumen: Síntesis estructurada de información clave
       - Comparación: Análisis contrastivo punto por punto
    2. Generación con LLM (Groq Llama 3.1 70B) para velocidad
    3. Extracción de fuentes utilizadas
    4. Formateo final con citas
    """
    
    def __init__(self):
        """Inicializa el agente RAG con LLM y prompts especializados."""
        logger.info("Inicializando RAGAgent...")
        
        # LLM para generación de respuestas (Groq - baja latencia)
        self.llm = llm_config.get_rag_llm()
        
        # LLM para respuestas generales (sin RAG)
        self.general_llm = llm_config.get_general_llm()
        
        # Prompts especializados por intención
        self.search_prompt = self._create_search_prompt()
        self.summary_prompt = self._create_summary_prompt()
        self.comparison_prompt = self._create_comparison_prompt()
        
        logger.info("RAGAgent inicializado con prompts especializados")
    
    def _create_search_prompt(self) -> ChatPromptTemplate:
        """
        Crea el prompt para búsquedas específicas.
        
        Objetivo: Respuestas precisas, concisas y bien fundamentadas.
        Incluye citas explícitas para cada afirmación.
        """
        return ChatPromptTemplate.from_messages([
            ("system", """Eres un asistente experto en proporcionar información precisa basada en documentos.

INSTRUCCIONES:
1. Responde la pregunta usando ÚNICAMENTE la información del contexto proporcionado
2. Sé preciso y conciso - ve directo al punto
3. SIEMPRE cita las fuentes usando el formato [Fuente X]
4. Si la información no está en el contexto, indica claramente que no se encontró
5. Organiza la respuesta de forma clara y estructurada
6. No inventes ni asumas información no presente en el contexto

FORMATO DE RESPUESTA:
- Respuesta directa a la pregunta
- Cada afirmación debe tener su cita [Fuente X]
- Si hay múltiples fuentes, cítalas todas

EJEMPLO:
"El COVID-19 se transmite principalmente por contacto cercano [Fuente 1]. Los síntomas más comunes incluyen fiebre y tos [Fuente 2]."

Contexto de documentos:
{context}

Pregunta del usuario: {query}

Responde de forma precisa y fundamentada:"""),
        ])
    
    def _create_summary_prompt(self) -> ChatPromptTemplate:
        """
        Crea el prompt para resúmenes.
        
        Objetivo: Síntesis estructurada que capture los puntos clave
        de múltiples documentos de forma coherente.
        """
        return ChatPromptTemplate.from_messages([
            ("system", """Eres un asistente experto en sintetizar información de múltiples documentos.

INSTRUCCIONES:
1. Lee todos los documentos del contexto proporcionado
2. Identifica y extrae los puntos clave más importantes
3. Organiza la información de forma lógica y estructurada
4. Usa viñetas o numeración para mayor claridad
5. Cita las fuentes de cada punto clave [Fuente X]
6. Elimina redundancias entre documentos
7. Mantén un tono objetivo y profesional

ESTRUCTURA RECOMENDADA:
- Introducción breve del tema
- Puntos clave principales (3-5)
- Detalles relevantes de cada punto
- Conclusión o síntesis final

FORMATO DE CITAS:
Cada punto importante debe referenciar sus fuentes [Fuente X, Y].

Contexto de documentos:
{context}

Tema a resumir: {query}

Genera un resumen completo y bien estructurado:"""),
        ])
    
    def _create_comparison_prompt(self) -> ChatPromptTemplate:
        """
        Crea el prompt para comparaciones.
        
        Objetivo: Análisis contrastivo claro que resalte
        similitudes, diferencias y características distintivas.
        """
        return ChatPromptTemplate.from_messages([
            ("system", """Eres un asistente experto en análisis comparativo de conceptos.

INSTRUCCIONES:
1. Identifica los elementos a comparar en la pregunta
2. Analiza el contexto para extraer información de cada elemento
3. Organiza la comparación de forma estructurada
4. Destaca similitudes Y diferencias de forma equilibrada
5. Usa tabla o formato punto por punto para claridad
6. Cita las fuentes para cada elemento comparado [Fuente X]
7. Sé objetivo y evita sesgos

ESTRUCTURA RECOMENDADA:
1. Breve descripción de cada elemento
2. Similitudes entre ambos
3. Diferencias clave (punto por punto)
4. Conclusión comparativa

FORMATO DE COMPARACIÓN:
**Elemento A:**
- Característica 1 [Fuente X]
- Característica 2 [Fuente Y]

**Elemento B:**
- Característica 1 [Fuente Z]
- Característica 2 [Fuente W]

Contexto de documentos:
{context}

Comparación solicitada: {query}

Genera un análisis comparativo completo:"""),
        ])
    
    def _format_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Formatea los documentos recuperados como contexto para el LLM.
        
        Args:
            documents: Lista de documentos con content y metadata
        
        Returns:
            String formateado con todos los documentos numerados
        """
        if not documents:
            return "No se encontraron documentos relevantes."
        
        context_parts = []
        for idx, doc in enumerate(documents, 1):
            content = doc.get('content', doc.get('page_content', ''))
            metadata = doc.get('metadata', {})
            source = metadata.get('source', 'Desconocida')
            
            # Formato: [Fuente X] - Contenido
            context_parts.append(
                f"[Fuente {idx}] (De: {source})\n{content}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def _extract_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Extrae la información de fuentes de los documentos.
        
        Args:
            documents: Lista de documentos con metadata
        
        Returns:
            Lista de diccionarios con información de fuentes
        """
        sources = []
        for idx, doc in enumerate(documents, 1):
            metadata = doc.get('metadata', {})
            sources.append({
                'id': f"Fuente {idx}",
                'source': metadata.get('source', 'Desconocida'),
                'chunk_index': metadata.get('chunk_index', 'N/A')
            })
        
        return sources
    
    def generate_response(self, 
                         query: str, 
                         documents: List[Dict[str, Any]], 
                         intent: str = "busqueda") -> Dict[str, Any]:
        """
        Genera una respuesta basada en documentos recuperados.
        
        Flujo:
        1. Selecciona el prompt adecuado según intención
        2. Formatea el contexto de documentos
        3. Genera respuesta con LLM
        4. Extrae fuentes utilizadas
        5. Retorna respuesta estructurada
        
        Args:
            query: Pregunta del usuario
            documents: Documentos recuperados por RetrieverAgent
            intent: Intención clasificada (busqueda, resumen, comparacion)
        
        Returns:
            Diccionario con response, sources, intent
        """
        logger.info(f"Generando respuesta RAG - Intent: {intent}, Docs: {len(documents)}")
        
        try:
            # Paso 1: Seleccionar prompt según intención
            if intent == "resumen":
                prompt_template = self.summary_prompt
                logger.info("Usando prompt de RESUMEN")
            elif intent == "comparacion":
                prompt_template = self.comparison_prompt
                logger.info("Usando prompt de COMPARACIÓN")
            else:  # busqueda o default
                prompt_template = self.search_prompt
                logger.info("Usando prompt de BÚSQUEDA")
            
            # Paso 2: Formatear contexto
            context = self._format_context(documents)
            
            # Paso 3: Generar respuesta
            messages = prompt_template.format_messages(
                context=context,
                query=query
            )
            
            response = self.llm.invoke(messages)
            response_text = response.content
            
            # Paso 4: Extraer fuentes
            sources = self._extract_sources(documents)
            
            logger.info(f"Respuesta generada exitosamente - Longitud: {len(response_text)} chars")
            
            return {
                "response": response_text,
                "sources": sources,
                "intent": intent,
                "num_documents_used": len(documents)
            }
            
        except Exception as e:
            logger.error(f"Error generando respuesta RAG: {str(e)}")
            return {
                "response": f"Error al generar respuesta: {str(e)}",
                "sources": [],
                "intent": intent,
                "error": str(e)
            }
    
    def generate_general_response(self, query: str) -> str:
        """
        Genera una respuesta general sin contexto RAG.
        
        Usado para consultas conversacionales, saludos, o preguntas
        que no requieren acceso a documentos.
        
        Args:
            query: Pregunta del usuario
        
        Returns:
            Respuesta directa del LLM
        """
        logger.info(f"Generando respuesta GENERAL (sin RAG) - Query: '{query[:50]}...'")
        
        try:
            # Prompt simple para conversación general
            prompt = ChatPromptTemplate.from_messages([
                ("system", """Eres un asistente conversacional amigable y útil.

Responde de forma natural, concisa y directa a preguntas generales.
Si la pregunta requiere información específica de documentos, indica que no tienes acceso a esa información.
Mantén un tono profesional pero cercano."""),
                ("user", "{query}")
            ])
            
            messages = prompt.format_messages(query=query)
            response = self.general_llm.invoke(messages)
            
            logger.info(f"Respuesta general generada - Longitud: {len(response.content)} chars")
            return response.content
            
        except Exception as e:
            logger.error(f"Error generando respuesta general: {str(e)}")
            return f"Lo siento, ocurrió un error al procesar tu consulta: {str(e)}"
    
    def format_response_with_sources(self, response_data: Dict[str, Any]) -> str:
        """
        Formatea la respuesta con las fuentes citadas al final.
        
        Añade una sección de "Fuentes consultadas" con la lista
        de documentos utilizados.
        
        Args:
            response_data: Diccionario con response y sources
        
        Returns:
            Texto formateado con respuesta y fuentes
        """
        response_text = response_data.get('response', '')
        sources = response_data.get('sources', [])
        
        if not sources:
            return response_text
        
        # Construir sección de fuentes
        sources_section = "\n\n--- Fuentes consultadas ---\n"
        for source in sources:
            sources_section += f"• {source['id']}: {source['source']}"
            if source.get('chunk_index') != 'N/A':
                sources_section += f" (Fragmento {source['chunk_index']})"
            sources_section += "\n"
        
        return response_text + sources_section
