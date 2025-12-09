"""Script de debug para probar el agente con LangChain 1.1"""
import os
from dotenv import load_dotenv
load_dotenv()

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

# Crear LLM de Gemini (el que falla)
print("Probando con Gemini...")
llm_gemini = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    temperature=0.1,
    max_tokens=500
)

# Crear tool simple
@tool
def classify_intent(query: str) -> dict:
    """Clasifica la intención del usuario en: busqueda, resumen, comparacion o general."""
    return {
        "intent": "busqueda",
        "confidence": 0.9,
        "requires_rag": True,
        "reasoning": "Query busca información específica"
    }

# Crear agente
print("Creando agente con Gemini...")
try:
    agent = create_agent(
        model=llm_gemini,
        tools=[classify_intent],
        system_prompt="Eres un clasificador de intenciones."
    )

    print(f"Tipo de agente: {type(agent)}")

    # Probar invocación con formato correcto
    print("\nProbando invocación...")
    result = agent.invoke({"messages": [{"role": "user", "content": "¿Qué es la diabetes?"}]})
    print(f"Resultado: {result}")
except Exception as e:
    print(f"Error con Gemini: {e}")
    import traceback
    traceback.print_exc()
