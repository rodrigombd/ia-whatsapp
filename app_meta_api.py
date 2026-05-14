import os
from flask import Flask, request, jsonify
import requests
import anthropic
from dotenv import load_dotenv

# 1. Cargar las variables del archivo .env
load_dotenv()

app = Flask(__name__)

# 2. Inicializar Claude usando la variable de entorno
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# 3. Credenciales de Meta desde el .env
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")

# RUTA GET: Meta usa esto para verificar el Webhook
@app.route("/webhook", methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("Webhook verificado correctamente por Meta")
            return challenge, 200
    return "Forbidden", 403

# RUTA POST: Aquí llegan los mensajes de WhatsApp
@app.route("/webhook", methods=['POST'])
def receive_message():
    data = request.json
    
    # CHIVATO: Imprimir todo lo que llegue para ver si Meta se comunica
    print("\nALGO HA LLEGADO DESDE META ")
    print(data)

    try:
        mensaje_usuario = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
        numero_usuario = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
    except KeyError:
        # Si llega un estado (Entregado, Leído), lo ignoramos pero avisamos
        print("ℹEra una confirmación de lectura o estado, no un mensaje de texto.")
        return jsonify({"status": "ok"}), 200

    print(f"Usuario {numero_usuario} dice: {mensaje_usuario}")

    # Preguntar a Claude
    try:
        respuesta_claude = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            messages=[{"role": "user", "content": mensaje_usuario}]
        )
        texto_respuesta = respuesta_claude.content[0].text
        print(f"Claude responde: {texto_respuesta}")
    except Exception as e:
        print(f"Error de Claude: {e}")
        texto_respuesta = "Lo siento, ha ocurrido un error al conectar con la IA."

    # Enviar respuesta a Meta
    url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero_usuario,
        "type": "text",
        "text": {"body": texto_respuesta}
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        print(f"Error enviando a Meta: {response.text}")
    else:
        print("Mensaje enviado de vuelta a WhatsApp con éxito")

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)