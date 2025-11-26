from google import genai
from dotenv import load_dotenv
import os

def load_AI_info_sucursal(solicitud):
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    try:
        client = genai.Client()
        print("✅ Cliente de Gemini inicializado correctamente usando la clave del .env")

        # The client gets the API key from the environment variable `GEMINI_API_KEY`.
        client = genai.Client()

        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=solicitud
        )
        
        # print(response.text)
        return response
        
    except ValueError as e:
        print(f"❌ Error al inicializar el cliente: {e}")
        print("Asegúrate de que la variable 'GEMINI_API_KEY' esté en tu archivo .env.")
        return e

