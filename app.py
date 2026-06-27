from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import http.client
import json

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metapython.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_y_hora = db.Column(db.DateTime, default=datetime.utcnow)
    texto = db.Column(db.Text)

with app.app_context():
    db.create_all()

def ordenar_por_fecha_y_hora(registros):
    return sorted(registros, key=lambda x: x.fecha_y_hora, reverse=True)

@app.route('/')
def index():
    registros = Log.query.all()
    registros_ordenados = ordenar_por_fecha_y_hora(registros)
    return render_template('index.html', registros=registros_ordenados)

def agregar_mensajes_log(texto):
    nuevo_registro = Log(texto=texto)
    db.session.add(nuevo_registro)
    db.session.commit()

TOKEN_CESAR = "cesar"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return verificar_token(request)
    elif request.method == 'POST':
        return recibir_mensajes(request)

def verificar_token(req):
    token = req.args.get('hub.verify_token')
    challenge = req.args.get('hub.challenge')
    if challenge and token == TOKEN_CESAR:
        return challenge
    return jsonify({'error': 'Token invalido'}), 401

def recibir_mensajes(req):
    try:
        data = req.get_json()
        entry = data['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        objeto_mensaje = value.get('messages')

        if objeto_mensaje:
            mensaje = objeto_mensaje[0]
            numero = mensaje.get("from")

            agregar_mensajes_log(json.dumps(mensaje, ensure_ascii=False))

            # Sin importar que tipo de mensaje sea (texto, audio, foto, lo que sea),
            # siempre respondemos con el logo + el saludo de bienvenida.
            enviar_bienvenida(numero)

        return jsonify({'message': 'EVENT_RECEIVED'}), 200

    except Exception as e:
        agregar_mensajes_log(f"Error: {str(e)}")
        return jsonify({'message': 'EVENT_RECEIVED'}), 200

def normalizar_numero_mx(numero):
    if numero.startswith("521") and len(numero) == 13:
        return "52" + numero[3:]
    return numero

def enviar_payload(data):
    data = json.dumps(data)
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer EAAVEa8dSzTcBR0MXYxCopzrf0Rg1MkPadQyFqKcZAuH237zFVA02BAeqAn84Y5nJnYZBokjXQZCT4esqIITG7fNvHZCTnbVZCWLA6JDQKfFfbDRF61nDStu3rYUIgBOmSpXZCRYWzQQfkfl1mSXE6YXzrRIqsZB7k0IJ6lzcDxo2Wl9ZBkxIwXamQSSmn2PUDZAOgC034CZC4M9giultqzZCBoj1QPru6V5hG6RQ7KU03Q4QeQGDfVJ8Doehp5gdwZBHYJqKuAnihTgEjPS4qb7mwoZAW5BZB3SKooUqzIhv7LngZDZD"
    }
    connection = http.client.HTTPSConnection("graph.facebook.com")
    try:
        connection.request("POST", "/v25.0/1158458244021223/messages", data, headers)
        response = connection.getresponse()
        response_body = response.read().decode('utf-8')
        agregar_mensajes_log(f"WhatsApp API -> Status: {response.status} {response.reason} | Body: {response_body}")
    except Exception as e:
        agregar_mensajes_log(f"Error de conexion: {str(e)}")
    finally:
        connection.close()

def enviar_bienvenida(number):
    number = normalizar_numero_mx(number)

    # 1. Mandamos primero la foto del logo
    data_imagen = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "image",
        "image": {
            "link": "https://github.com/bocalapaz-lab/chatbot/blob/main/logo%20boca_page-0001.jpg?raw=true"
        }
    }
    enviar_payload(data_imagen)

    # 2. Justo despues, mandamos el mensaje de bienvenida
    data_bienvenida = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": "¡Hola! 👋 Gracias por escribirnos a *BOCA*."
        }
    }
    enviar_payload(data_bienvenida)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)