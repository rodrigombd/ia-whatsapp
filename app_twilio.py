from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import anthropic
from dotenv import load_dotenv

# 1. Cargar las variables del archivo .env
load_dotenv()

app = Flask(__name__)


client = anthropic.Anthropic("ANTHROPIC_API_KEY")

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    # 1. Recibir el mensaje de WhatsApp desde Twilio
    mensaje_usuario = request.values.get('Body', '')
    
    # 2. Enviar el mensaje a Claude
    try:
        respuesta_claude = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": mensaje_usuario}
            ]
        )
        texto_respuesta = respuesta_claude.content[0].text
    except Exception as e:
        texto_respuesta = "Lo siento, ha ocurrido un error al conectar con Claude."

    # 3. Formatear la respuesta para que Twilio se la mande a WhatsApp
    resp = MessagingResponse()
    resp.message(texto_respuesta)
    
    return str(resp)

if __name__ == "__main__":
    # Arranca el servidor en el puerto 5000
    app.run(port=5000, debug=True)