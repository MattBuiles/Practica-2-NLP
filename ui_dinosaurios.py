"""
UI básica con Streamlit para probar los 10 casos de uso del sistema RAG de Dinosaurios.
"""
import streamlit as st
import time
from datetime import datetime
import json
from pathlib import Path

# Configurar página
st.set_page_config(
    page_title="🦖 RAG Dinosaurios",
    page_icon="🦖",
    layout="wide"
)

# Casos de uso predefinidos
CASOS_DE_USO = [
    {
        "numero": 1,
        "categoria": "Información General",
        "query": "¿Cuáles fueron los dinosaurios más grandes que existieron?",
        "descripcion": "Consulta sobre tamaño de dinosaurios"
    },
    {
        "numero": 2,
        "categoria": "Anatomía",
        "query": "¿Cómo usaba sus brazos el Tyrannosaurus rex?",
        "descripcion": "Consulta específica sobre T-Rex"
    },
    {
        "numero": 3,
        "categoria": "Evolución",
        "query": "¿Cómo evolucionaron las aves a partir de los dinosaurios?",
        "descripcion": "Relación evolutiva aves-dinosaurios"
    },
    {
        "numero": 4,
        "categoria": "Comportamiento",
        "query": "¿Fueron los dinosaurios buenos padres?",
        "descripcion": "Cuidado parental en dinosaurios"
    },
    {
        "numero": 5,
        "categoria": "Comparación",
        "query": "¿Cuáles son las diferencias entre dinosaurios carnívoros y herbívoros?",
        "descripcion": "Comparación de tipos de dinosaurios"
    },
    {
        "numero": 6,
        "categoria": "Descubrimientos",
        "query": "¿Qué pasa cuando encuentras un dinosaurio?",
        "descripcion": "Proceso de descubrimiento paleontológico"
    },
    {
        "numero": 7,
        "categoria": "Extinción",
        "query": "¿Cómo afectó la extinción de los dinosaurios a otros animales?",
        "descripcion": "Impacto de la extinción masiva"
    },
    {
        "numero": 8,
        "categoria": "Defensa",
        "query": "¿Para qué usaban los Ankylosaurs sus colas con mazas?",
        "descripcion": "Mecanismos de defensa"
    },
    {
        "numero": 9,
        "categoria": "Ecosistemas",
        "query": "¿Qué animales convivían con los dinosaurios?",
        "descripcion": "Fauna del Mesozoico"
    },
    {
        "numero": 10,
        "categoria": "Resumen",
        "query": "Resume la información disponible sobre trilobites",
        "descripcion": "Resumen de documentos sobre trilobites"
    }
]


@st.cache_resource
def cargar_orchestrator():
    """Carga el orchestrator una sola vez."""
    from src.agents.autonomous_orchestrator import AutonomousOrchestrator
    return AutonomousOrchestrator()


def main():
    st.title("🦖 Sistema RAG - Dinosaurios")
    st.markdown("---")
    
    # Sidebar con casos de uso
    st.sidebar.header("📋 Casos de Uso")
    
    # Selector de caso
    caso_seleccionado = st.sidebar.selectbox(
        "Selecciona un caso de prueba:",
        options=range(len(CASOS_DE_USO)),
        format_func=lambda x: f"#{CASOS_DE_USO[x]['numero']}: {CASOS_DE_USO[x]['categoria']}"
    )
    
    caso = CASOS_DE_USO[caso_seleccionado]
    
    # Mostrar info del caso
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Categoría:** {caso['categoria']}")
    st.sidebar.markdown(f"**Descripción:** {caso['descripcion']}")
    
    # Opción de query personalizada
    st.sidebar.markdown("---")
    usar_custom = st.sidebar.checkbox("Usar query personalizada")
    
    # Área principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"📝 Caso #{caso['numero']}: {caso['categoria']}")
        
        if usar_custom:
            query = st.text_area(
                "Escribe tu consulta:",
                value="",
                height=100,
                placeholder="Escribe tu pregunta sobre dinosaurios..."
            )
        else:
            query = st.text_area(
                "Query del caso de uso:",
                value=caso['query'],
                height=100,
                disabled=True
            )
            query = caso['query']
        
        # Botón de ejecutar
        ejecutar = st.button("🚀 Ejecutar Consulta", type="primary", use_container_width=True)
    
    with col2:
        st.subheader("⚙️ Estado del Sistema")
        
        # Estado de inicialización
        if 'orchestrator' not in st.session_state:
            st.warning("⏳ Sistema no inicializado")
            if st.button("🔧 Inicializar Sistema"):
                with st.spinner("Cargando orchestrator..."):
                    try:
                        st.session_state.orchestrator = cargar_orchestrator()
                        st.success("✅ Sistema listo")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        else:
            st.success("✅ Sistema inicializado")
            st.info("📊 6054 documentos indexados")
    
    st.markdown("---")
    
    # Ejecutar consulta
    if ejecutar:
        if 'orchestrator' not in st.session_state:
            st.error("⚠️ Primero debes inicializar el sistema")
        elif not query.strip():
            st.warning("⚠️ Por favor ingresa una consulta")
        else:
            # Contenedor de resultados
            result_container = st.container()
            
            with result_container:
                st.subheader("🔄 Procesando consulta...")
                
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Pasos del proceso
                steps = [
                    "Clasificando intención...",
                    "Decidiendo estrategia...",
                    "Recuperando documentos...",
                    "Generando respuesta...",
                    "Validando respuesta..."
                ]
                
                start_time = time.time()
                
                try:
                    # Simular progreso mientras procesa
                    for i, step in enumerate(steps):
                        status_text.text(f"📍 Paso {i+1}/5: {step}")
                        progress_bar.progress((i + 1) * 20)
                        
                        if i == 0:
                            # Ejecutar consulta real
                            result = st.session_state.orchestrator.process_query(query)
                        time.sleep(0.1)
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Completado")
                    
                    end_time = time.time()
                    execution_time = end_time - start_time
                    
                    # Mostrar resultados
                    st.markdown("---")
                    st.subheader("💬 Respuesta")
                    
                    # Respuesta en un cuadro destacado
                    st.markdown(f"""
                    <div style="background-color: #1e1e1e; padding: 20px; border-radius: 10px; border-left: 4px solid #4CAF50;">
                    {result.get('response', 'Sin respuesta')}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Métricas
                    st.markdown("---")
                    st.subheader("📊 Métricas")
                    
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    
                    with col_m1:
                        st.metric("Intención", result.get('intent', 'N/A'))
                    
                    with col_m2:
                        st.metric("Estrategia", result.get('strategy', 'N/A'))
                    
                    with col_m3:
                        st.metric("Documentos", result.get('documents_used', 0))
                    
                    with col_m4:
                        validation_score = result.get('validation', {}).get('confidence_score', 0)
                        st.metric("Validación", f"{validation_score:.0%}")
                    
                    # Tiempo de ejecución
                    st.info(f"⏱️ Tiempo de ejecución: {execution_time:.2f} segundos")
                    
                    # Detalles expandibles
                    with st.expander("🔍 Ver detalles de la traza"):
                        st.json({
                            "query": query,
                            "intent": result.get('intent'),
                            "strategy": result.get('strategy'),
                            "documents_used": result.get('documents_used'),
                            "validation": result.get('validation'),
                            "execution_time": execution_time,
                            "timestamp": datetime.now().isoformat()
                        })
                    
                    # Guardar en historial
                    if 'historial' not in st.session_state:
                        st.session_state.historial = []
                    
                    st.session_state.historial.append({
                        "timestamp": datetime.now().isoformat(),
                        "query": query,
                        "response": result.get('response', '')[:200],
                        "intent": result.get('intent'),
                        "time": execution_time
                    })
                    
                except Exception as e:
                    st.error(f"❌ Error al procesar: {str(e)}")
                    progress_bar.empty()
                    status_text.empty()
    
    # Historial de consultas
    st.markdown("---")
    with st.expander("📜 Historial de consultas"):
        if 'historial' in st.session_state and st.session_state.historial:
            for i, h in enumerate(reversed(st.session_state.historial[-5:])):
                st.markdown(f"""
                **{h['timestamp'][:19]}** - *{h['intent']}* ({h['time']:.1f}s)
                > {h['query'][:100]}...
                """)
                st.markdown("---")
        else:
            st.info("No hay consultas en el historial")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: gray; font-size: 12px;">
    🦖 Sistema RAG de Dinosaurios | Práctica 2 NLP | 2025
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
