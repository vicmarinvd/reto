"""
Widget de chat flotante con DigiBot - Asistente inteligente de riesgo
"""
import streamlit as st
from datetime import datetime
from typing import Optional, Dict
from geminiPrueba import chat_with_digibot


def render_chat_widget(current_context: Optional[Dict] = None):
    """
    Renderiza el widget de chat flotante con DigiBot
    
    Args:
        current_context: Diccionario con información de la sucursal actual y dataset completo
    """
    # Inicializar estado del chat si no existe
    if 'chat_open' not in st.session_state:
        st.session_state.chat_open = False
    
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'pending_message' not in st.session_state:
        st.session_state.pending_message = None
    
    # CSS para chat flotante en esquina inferior derecha
    st.markdown("""
    <style>
    [data-testid="stChatMessageContent"] {
        padding: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Renderizar chat como sidebar flotante
    if st.session_state.chat_open:
        # Crear contenedor flotante
        with st.sidebar:
            st.markdown("### 🤖 DigiBot")
            
            # Botón cerrar
            if st.button("✖ Cerrar", key="close_chat", use_container_width=True):
                st.session_state.chat_open = False
                st.rerun()
            
            st.markdown("---")
            
            # Contenedor de mensajes
            chat_container = st.container(height=400)
            
            with chat_container:
                if len(st.session_state.chat_messages) == 0:
                    st.info("👋 Hola! Pregúntame sobre las sucursales, riesgos o comparaciones.")
                else:
                    for msg in st.session_state.chat_messages:
                        with st.chat_message(msg['role']):
                            st.write(msg['text'])
            
            # Input de usuario
            user_input = st.chat_input("Escribe tu pregunta...")
            
            # Procesar mensaje SOLO si hay uno nuevo
            if user_input and user_input != st.session_state.pending_message:
                st.session_state.pending_message = user_input
                
                # Agregar mensaje del usuario
                st.session_state.chat_messages.append({
                    'role': 'user',
                    'text': user_input
                })
                
                # Preparar contexto con info del dataset
                if current_context:
                    sucursal_actual = current_context.get('sucursal_actual', {})
                    context_string = f"""
Información de la sucursal actual:
- Sucursal: {sucursal_actual.get('Sucursal', 'N/A')}
- Cluster: {sucursal_actual.get('Cluster_KM', 'N/A')}
- Nivel de Riesgo: {sucursal_actual.get('Nivel_Riesgo', 'N/A')}
- FPD Neto: {sucursal_actual.get('FPD_Neto_Actual', 0)}%
- ICV: {sucursal_actual.get('ICV_Actual', 0)}%
- Score de Riesgo: {sucursal_actual.get('Score_Riesgo', 0)}

Información general del dataset:
- Total de sucursales: {current_context.get('total_sucursales', 0)}
- Sucursales en alto riesgo: {current_context.get('sucursales_alto_riesgo', 0)}
- Promedio FPD: {current_context.get('promedio_fpd', 0):.2f}%
- Promedio ICV: {current_context.get('promedio_icv', 0):.2f}%

Tienes acceso a información de todas las sucursales. El usuario puede preguntarte por comparaciones o información de otras sucursales.
"""
                else:
                    context_string = "El usuario está en el dashboard general."
                
                # Obtener respuesta de DigiBot
                with st.spinner("Pensando..."):
                    response_text = chat_with_digibot(
                        st.session_state.chat_history,
                        user_input,
                        context_string
                    )
                
                # Agregar respuesta del bot
                st.session_state.chat_messages.append({
                    'role': 'assistant',
                    'text': response_text
                })
                
                # Actualizar historial
                st.session_state.chat_history.append({
                    'role': 'user',
                    'parts': [{'text': user_input}]
                })
                st.session_state.chat_history.append({
                    'role': 'model',
                    'parts': [{'text': response_text}]
                })
                
                st.rerun()
            
            # Botón limpiar
            if st.button("🗑️ Limpiar chat", use_container_width=True):
                st.session_state.chat_messages = []
                st.session_state.chat_history = []
                st.session_state.pending_message = None
                st.rerun()
    
    # Botón flotante para abrir chat (siempre visible en esquina)
    if not st.session_state.chat_open:
        # Usar columnas para posicionar en esquina
        col1, col2, col3 = st.columns([5, 1, 1])
        with col3:
            if st.button("💬", key="open_chat", help="Abrir DigiBot", use_container_width=True):
                st.session_state.chat_open = True
                st.rerun()


def reset_chat():
    """Reinicia el chat eliminando todos los mensajes"""
    st.session_state.chat_messages = []
    st.session_state.chat_history = []
    st.session_state.pending_message = None