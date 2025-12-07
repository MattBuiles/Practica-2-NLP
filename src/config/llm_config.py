"""
Configuración de LLMs para diferentes agentes del sistema.
Justificación de uso de Gemini vs Groq por agente.
"""
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class LLMConfig:
    """
    Configuración centralizada de LLMs para el sistema Agentic AI.
    
    Justificación de selección:
    - Gemini: Mejor comprensión contextual y razonamiento profundo
    - Groq: Latencia mínima y velocidad de respuesta
    """
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GOOGLE_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        
        if not self.gemini_api_key:
            raise ValueError("GOOGLE_API_KEY no encontrada en variables de entorno")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY no encontrada en variables de entorno")
    
    def get_classifier_llm(self):
        """
        LLM para el Agente Clasificador.
        Usa Gemini por su superior capacidad de interpretación contextual.
        """
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=self.gemini_api_key,
            temperature=0.1,  # Baja temperatura para clasificación consistente
            max_tokens=500
        )
    
    def get_retriever_llm(self):
        """
        LLM para el Agente Recuperador.
        Usa Groq para optimización rápida de consultas.
        """
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            groq_api_key=self.groq_api_key,
            temperature=0.2,
            max_tokens=1000
        )
    
    def get_rag_llm(self):
        """
        LLM para el Agente RAG (generación de respuestas).
        Usa Groq por su latencia mínima y velocidad.
        """
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            groq_api_key=self.groq_api_key,
            temperature=0.3,
            max_tokens=2000
        )
    
    def get_critic_llm(self):
        """
        LLM para el Agente Crítico/Verificador.
        Usa Gemini por su capacidad de razonamiento profundo.
        """
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=self.gemini_api_key,
            temperature=0.1,
            max_tokens=1500
        )
    
    def get_orchestrator_llm(self):
        """
        LLM para el Orquestador.
        Usa Groq para decisiones rápidas de coordinación.
        """
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            groq_api_key=self.groq_api_key,
            temperature=0.1,
            max_tokens=1000
        )
    
    def get_general_llm(self):
        """
        LLM para consultas generales (sin RAG).
        Usa Groq por velocidad.
        """
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            groq_api_key=self.groq_api_key,
            temperature=0.5,
            max_tokens=1500
        )


# Instancia global
llm_config = LLMConfig()
