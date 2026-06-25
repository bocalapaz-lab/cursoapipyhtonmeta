from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import http.client
import json

app = Flask(__name__)

# Configuración de la base de datos SQLITE
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metapython.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de la tabla log
class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_y_hora = db.Column(db.DateTime, default=datetime.utcnow)
    texto = db.Column(db.Text)

# Crear la tabla si no existe
with app.app_context():
    db.create_all()

# Función para ordenar los registros por fecha y hora
def ordenar_por_fecha_y_hora(registros):
    return sorted(registros, key=lambda x: x.fecha_y_hora, reverse=True)

@app.route('/')
def index():
    registros = Log.query.all()
    registros_ordenados = ordenar_por_fecha_y_hora(registros)
    return render_template('index.html', registros=registros_ordenados)

mensajes_log = []

# Función para agregar mensajes y guardar en la base de datos
def agregar_mensajes_log(texto):
    mensajes_log.append(texto)

    nuevo_registro = Log(texto=texto)
    db.session.add(nuevo_registro)
    db.session.commit()

# Token de verificación para la configuración
TOKEN_CESAR = "cesar"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        challenge = verificar_token(request)
        return challenge
    elif request.method == 'POST':
        response = recibir_mensajes(request)
        return response

def verificar_token(req):
    token = req.args.get('hub.verify_token')
    challenge = req.args.get('hub.challenge')

    if challenge and token == TOKEN_CESAR:
        return challenge
    else:
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

            if "type" in mensaje:
                tipo = mensaje["type"]

                if tipo == "interactive":
                    return jsonify({'message': 'EVENT_RECEIVED'}), 200

                if "text" in mensaje:
                    texto = mensaje["text"]["body"]
                    numero = mensaje["from"]

                    agregar_mensajes_log(json.dumps(objeto_mensaje, ensure_ascii=False))
                    enviar_mensajes_whatsapp(texto, numero)

        return jsonify({'message': 'EVENT_RECEIVED'}), 200

    except Exception as e:
        agregar_mensajes_log(str(e))
        return jsonify({'message': 'EVENT_RECEIVED'}), 200

def enviar_mensajes_whatsapp(texto, number):
    texto = texto.lower()

    if "hola" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "🚀 Hola, ¿Cómo estás? Bienvenido."
            }
        }
    else:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Menu de opciones"
            }
        }

    data = json.dumps(data)

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer EAAVEa8dSzTcBR2sGjvAh6ROHu1F8UlfZAFTsOMbd9F333oxMdVwUDa9g8StTpUUIOTZBUpkpUAmUAOvfvRmicyZC4fsrl0kVXpofIKeERLndZCsFElr7ieZCRKVjaHZCdMkmizxepa4SzNgEMuOHYwiiyqRVZAOqcdqtxkHYYQFGzvK5tB0GqUIt02vsNgdUoKa8itNjP7AT08m0EmmRfFOv1d7K3tWcfkZBYOyXVJILJ8nAOcDhZArcHMZC3rOZCteYEuJCtXy33uKsSPXHusdhZBpzfnmG0w1AdgHeZABQ6dwZDZD"
    }

    connection = http.client.HTTPSConnection("graph.facebook.com")

    try:
        connection.request("POST", "/v25.0/1158458244021223/messages", data, headers)
        response = connection.getresponse()
        print(response.status, response.reason)
    except Exception as e:
        agregar_mensajes_log(str(e))
    finally:
        connection.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
