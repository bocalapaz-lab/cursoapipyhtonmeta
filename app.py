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

                agregar_mensajes_log(json.dumps(tipo))


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

# Corrige el formato de numeros mexicanos: el webhook manda "521XXXXXXXXXX"
# (13 digitos, con un "1" extra despues del codigo de pais 52), pero para
# ENVIAR mensajes Meta espera "52XXXXXXXXXX" (12 digitos, sin el "1").
def normalizar_numero_mx(numero):
    if numero.startswith("521") and len(numero) == 13:
        return "52" + numero[3:]
    return numero

def enviar_mensajes_whatsapp(texto, number):
    texto = texto.lower()
    number = normalizar_numero_mx(number)

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
    
    elif "1" in texto: 
        data  = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "ey, como estamos"
            }
        }

    elif "2" in texto: 
        data  = {
                "messaging_product": "whatsapp",
                "to": number,
                "type": "location",
                "location": {
                    "latitude": "-12.067158831865067",
                    "longitude": "-77.03377940839486",
                    "name": "Estadio Nacional del Perú",
                    "address": "Cercado de Lima"
                }
            }

    elif "3" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "document",
            "document": {
                    "link": "https://www.soundczech.cz/temp/lorem-ipsum.pdf",
                    "caption": "Temario del Curso #001"
        }
    }

    elif "4" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "audio",
            "audio": {
                "link": "https://filesamples.com/samples/audio/mp3/sample1.mp3"
        }
    }

    elif "5" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": True,
                "body": "Introduccion al curso! https://youtu.be/6ULOE2tGlBM"
        }
    }

    elif "6" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "💖 En breve me pondré en contacto contigo. 😎"
        }
    }
        
    elif "7" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "📅 Horario de Atención: Lunes a Viernes.\n📞 Horario: 9:00 am a 5:00 ..."
        }
    }
        
    elif "0" in texto:
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

    elif "boton" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": "¿Confirmas tu registro?"
                },
                "footer": {
                    "text": "Selecciona una de las opciones"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "btnsi",
                                "title": "Si"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "btnno",
                                "title": "No"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "btntalvez",
                                "title": "Tal Vez"
                        }
                    }
                ]
            }
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
        "Authorization": "Bearer EAAVEa8dSzTcBR6YZCaDpopNnqZBOJZCAtZBj9rzu03y1EWVZC1mxofA7QGZBpesCOiyKxRFhoZBa4dYic4oZBAcnTI2WRZCgSwW9Xg0aZBCz8kgnRGvcEFubiKErz3ZCtYOxaBYPWqD1TyZCThcwAVZCdxPdiAZBZB9B6NhgJ1bC6YSNqUuZBFGfdvFJP776cxZCW01N1LUEmcZC8JOTZAFXwBSAGIz4JZCGnahZBEnM9WuTbOqo2WlZBoIlGppSbqyEZCB9PuMa7ZBs0HGZCI35qEXRBZCsgKqdYWvSoMUYDayk3LgkzpCnr6agZDZD"
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)