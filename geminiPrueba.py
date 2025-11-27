# from google import genai
# from dotenv import load_dotenv
# import os

# def load_AI_info_sucursal(solicitud):
#     load_dotenv()
#     api_key = os.getenv("GEMINI_API_KEY")
    
#     try:
#         client = genai.Client()
#         print("✅ Cliente de Gemini inicializado correctamente usando la clave del .env")

#         # The client gets the API key from the environment variable `GEMINI_API_KEY`.
#         client = genai.Client()

#         response = client.models.generate_content(
#             model="gemini-2.5-flash", 
#             contents=solicitud
#         )
        
#         # print(response.text)
#         return response
        
#     except ValueError as e:
#         print(f"❌ Error al inicializar el cliente: {e}")
#         print("Asegúrate de que la variable 'GEMINI_API_KEY' esté en tu archivo .env.")
#         return e


from google import genai
from dotenv import load_dotenv
import os
import json

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
    """
    Genera análisis de sucursal usando Gemini AI
    
    Args:
        solicitud: String con la solicitud de análisis
        
    Returns:
        Response object de Gemini o Exception en caso de error
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    try:
        client = genai.Client()
        print("✅ Cliente de Gemini inicializado correctamente usando la clave del .env")

        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=solicitud
        )
        
        return response
        
    except ValueError as e:
        print(f"❌ Error al inicializar el cliente: {e}")
        print("Asegúrate de que la variable 'GEMINI_API_KEY' esté en tu archivo .env.")
        return e


def analyze_branch_with_gemini(sucursal_data):
    """
    Analiza una sucursal específica usando Gemini AI
    
    Args:
        sucursal_data: Diccionario con datos de la sucursal
        
    Returns:
        Diccionario con causes, suggestions y riskFactor
    """
    load_dotenv()
    
    prompt = f"""
    Analiza la sucursal: {sucursal_data.get('Sucursal', 'N/A')}
    Datos:
    Cluster: {sucursal_data.get('Cluster_KM', 'N/A')}
    Región: {sucursal_data.get('Región', 'N/A')}
    FPD Neto: {sucursal_data.get('FPD_Neto_Actual', 0)}%
    ICV: {sucursal_data.get('ICV_Actual', 0)}%
    Morosidad: {sucursal_data.get('Tasa_Morosidad', 0)}%
    Score Riesgo: {sucursal_data.get('Score_Riesgo', 0)}

    Genera:
    1. Una lista de 5 posibles causas EXACTAS del riesgo o estado actual. (Máx 10 palabras c/u).
    2. Una lista de 6 sugerencias de mejora concretas. (Máx 10 palabras c/u).
    3. Identifica cual es el factor de riesgo número uno.
    
    Responde ÚNICAMENTE con un objeto JSON válido con esta estructura:
    {{
        "causes": ["causa1", "causa2", "causa3", "causa4", "causa5"],
        "suggestions": ["sugerencia1", "sugerencia2", "sugerencia3", "sugerencia4", "sugerencia5", "sugerencia6"],
        "riskFactor": "el indicador o factor que más pone en riesgo a la sucursal"
    }}
    """
    
    try:
        client = genai.Client()
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "system_instruction": DIGIBOT_SYSTEM_INSTRUCTION,
                "response_mime_type": "application/json",
                "temperature": 0.4,
            }
        )
        
        # Parsear respuesta JSON
        analysis = json.loads(response.text)
        return analysis
        
    except Exception as e:
        print(f"❌ Error al analizar sucursal: {e}")
        return {
            "causes": ["Error al conectar con DigiBot", "Verifique su API Key", "Intente nuevamente"],
            "suggestions": ["Revisar configuración", "Contactar soporte"],
            "riskFactor": "Desconocido"
        }


def chat_with_digibot(history, new_message, context_data=""):
    """
    Mantiene una conversación con DigiBot
    
    Args:
        history: Lista de mensajes previos en formato [{'role': 'user/model', 'parts': [{'text': '...'}]}]
        new_message: Nuevo mensaje del usuario
        context_data: Contexto adicional (datos de sucursal actual, etc.)
        
    Returns:
        String con la respuesta de DigiBot
    """
    load_dotenv()
    
    system_instruction = DIGIBOT_SYSTEM_INSTRUCTION
    if context_data:
        system_instruction += f"\n\nContexto actual de datos en pantalla:\n{context_data}"
    
    try:
        client = genai.Client()
        
        # Crear chat con historial
        chat = client.chats.create(
            model="gemini-2.5-flash",
            config={
                "system_instruction": system_instruction,
                "temperature": 0.7,
            },
            history=history
        )
        
        # Enviar nuevo mensaje
        result = chat.send_message(message=new_message)
        return result.text
        
    except Exception as e:
        print(f"❌ Error en chat: {e}")
        return "Lo siento, tuve un problema al procesar tu solicitud. Por favor verifica tu conexión o API Key."