
from google import genai
from dotenv import load_dotenv
import os
import json
# import streamlit as st

# st.write("La API key existe:", "GEMINI_API_KEY" in st.secrets)

def get_gemini_key():
    load_dotenv()
    import streamlit as st

    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("❌ GEMINI_API_KEY no está configurada en st.secrets ni en el .env")

    return api_key


# Instrucciones del sistema para DigiBot
DIGIBOT_SYSTEM_INSTRUCTION = """
Rol del Agente: DigiBot
Eres el Asistente Inteligente de Riesgo Operativo y Crédito de Kernel Capital (Dimex).
Tu propósito es explicar el cluster de cada sucursal, identificar variables influyentes, interpretar KPIs, generar insights accionables y responder preguntas de negocio.

Reglas de Estilo:
1. Estilo factual y analítico. Basado en datos.
2. Orientado a acciones. Diagnóstico -> Acción.
3. Tono profesional ejecutivo.

Inputs: Recibirás datos de sucursales (KPIs, Clusters).
Clusters:
- Normal: Desempeño estable.
- Premium: Alto desempeño.
- Riesgo: Deterioro, alta probabilidad de pérdidas.
"""
def load_AI_info_sucursal(solicitud):
    api_key = get_gemini_key()

    try:
        client = genai.Client(api_key=api_key)
        print("✅ Cliente de Gemini inicializado correctamente")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=solicitud
        )
        return response

    except Exception as e:
        print(f"❌ Error al inicializar Gemini: {e}")
        return e


def analyze_branch_with_gemini(sucursal_data):
    api_key = get_gemini_key()

    prompt = f""" ... """

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "system_instruction": DIGIBOT_SYSTEM_INSTRUCTION,
                "response_mime_type": "application/json",
                "temperature": 0.4,
            }
        )

        return json.loads(response.text)

    except Exception as e:
        print(f"❌ Error al analizar sucursal: {e}")
        return {
            "causes": ["Error al conectar con DigiBot", "Verifique su API Key", "Intente nuevamente"],
            "suggestions": ["Revisar configuración", "Contactar soporte"],
            "riskFactor": "Desconocido"
        }


def chat_with_digibot(history, new_message, context_data=""):
    api_key = get_gemini_key()

    system_instruction = DIGIBOT_SYSTEM_INSTRUCTION
    if context_data:
        system_instruction += f"\n\nContexto actual de datos en pantalla:\n{context_data}"

    try:
        client = genai.Client(api_key=api_key)

        chat = client.chats.create(
            model="gemini-2.5-flash",
            config={
                "system_instruction": system_instruction,
                "temperature": 0.7,
            },
            history=history
        )

        result = chat.send_message(message=new_message)
        return result.text

    except Exception as e:
        print(f"❌ Error en chat: {e}")
        return "Lo siento, tuve un problema al procesar tu solicitud. Por favor verifica tu conexión o API Key."
