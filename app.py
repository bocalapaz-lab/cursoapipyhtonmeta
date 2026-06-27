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

# Token de verificación para la configuración del webhook (esto NO es el token de envío)
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
            tipo = mensaje.get("type")

            agregar_mensajes_log(json.dumps(mensaje, ensure_ascii=False))

            if tipo == "text":
                texto = mensaje["text"]["body"]
                enviar_mensajes_whatsapp(texto, numero)
            else:
                # Si mandan audio, imagen, sticker, ubicacion, etc. -> tambien mandamos el menu
                enviar_menu_bienvenida(numero)

        return jsonify({'message': 'EVENT_RECEIVED'}), 200

    except Exception as e:
        agregar_mensajes_log(f"Error: {str(e)}")
        return jsonify({'message': 'EVENT_RECEIVED'}), 200

# Corrige el formato de numeros mexicanos: el webhook manda "521XXXXXXXXXX"
# (con un "1" extra despues del codigo de pais 52), pero para ENVIAR
# mensajes Meta espera "52XXXXXXXXXX" (sin el "1").
def normalizar_numero_mx(numero):
    if numero.startswith("521") and len(numero) == 13:
        return "52" + numero[3:]
    return numero

def enviar_payload(data):
    data = json.dumps(data)
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer EAAVEa8dSzTcBR0dNxUoIc02ZBZCm1MZAoTOM3SZCZCx5olkQJOm51DGTQWiP19JCnXkQDJI0z30erTGUOASXA6L0kEkIwalZBZAWMHGELptnEJakOguFmW8aMZCXe1MCISC693ZBbaPpr08Ueq5VMnF6TpTuMOyLR40d8KLOiOyWvRIfkIlq5wK588aas74b7taJDmiOVXpwLubzcYBK4UPdwqI6Cqd66ecyVWesg9eHcvJd4kOOphnA0gZANIUIIE8XLfZC21TfwAIjPQZBpBbcTkWYlayZBBxobLhnZBiml5GgZDZD"  # TODO: pon tu token de System User
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

def enviar_menu_bienvenida(number):
    number = normalizar_numero_mx(number)
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": (
                "¡Hola! 👋 Gracias por escribirnos a *BOCA*.\n\n"
                "Soy el asistente virtual y estoy aquí para ayudarte mientras "
                "un miembro de nuestro equipo te atiende personalmente.\n\n"
                "Elige una opción escribiendo el número:\n\n"
                "1️⃣ Conócenos: nuestro equipo y experiencia\n"
                "2️⃣ Video de nuestras instalaciones\n"
                "3️⃣ Ubicación del consultorio\n"
                "4️⃣ Estacionamiento\n\n"
                "Escribe el número de la opción que te interese 😊"
            )
        }
    }
    enviar_payload(data)

def enviar_mensajes_whatsapp(texto, number):
    texto = texto.strip().lower()
    number = normalizar_numero_mx(number)

    if texto == "1":
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": (
                    "👋 *¡Bienvenido a BOCA!*\n\n"
                    "Somos un equipo de profesionales dedicados a tu salud, "
                    "comprometidos con brindarte la mejor atención.\n\n"
                    "👨‍⚕️ *Dr. [NOMBRE DEL DOCTOR]*\n"
                    "[Especialidad, cédula profesional, años de experiencia]\n\n"
                    "👩‍⚕️ *Dra. [NOMBRE DE LA DOCTORA]*\n"
                    "[Especialidad, cédula profesional, años de experiencia]\n\n"
                    "[Aquí puedes agregar misión, valores, certificaciones, "
                    "tecnología que usan, etc.]\n\n"
                    "Escribe *0* para volver al menú. 😊"
                )
            }
        }
        enviar_payload(data)

    elif texto == "2":
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": True,
                "body": (
                    "🎥 Conoce nuestras instalaciones y a nuestro equipo en BOCA:\n"
                    "TODO_PON_AQUI_EL_LINK_DEL_VIDEO\n\n"
                    "Escribe *0* para volver al menú."
                )
            }
        }
        enviar_payload(data)

    elif texto == "3":
        data = {
            "messaging_product": "whatsapp",
            "to": number,
            "type": "location",
            "location": {
                "latitude": "TODO_LATITUD_DEL_CONSULTORIO",
                "longitude": "TODO_LONGITUD_DEL_CONSULTORIO",
                "name": "BOCA",
                "address": "TODO_DIRECCION_COMPLETA_DEL_CONSULTORIO"
            }
        }
        enviar_payload(data)

    elif texto == "4":
        # 1) Mandamos la ubicación del estacionamiento sugerido
        data_ubicacion = {
            "messaging_product": "whatsapp",
            "to": number,
            "type": "location",
            "location": {
                "latitude": "TODO_LATITUD_ESTACIONAMIENTO",
                "longitude": "TODO_LONGITUD_ESTACIONAMIENTO",
                "name": "Estacionamiento sugerido",
                "address": "TODO_DIRECCION_DEL_ESTACIONAMIENTO"
            }
        }
        enviar_payload(data_ubicacion)

        # 2) Mandamos el aviso/descargo de responsabilidad
        data_aviso = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": (
                    "🅿️ Nuestro consultorio no cuenta con estacionamiento propio "
                    "ni en la vía pública. Te recomendamos el estacionamiento "
                    "ubicado cruzando la calle (ubicación enviada arriba 👆).\n\n"
                    "⚠️ Este estacionamiento es un servicio independiente. "
                    "*BOCA no se hace responsable* por el vehículo, sus "
                    "pertenencias, ni por el servicio que ahí se preste.\n\n"
                    "Escribe *0* para volver al menú."
                )
            }
        }
        enviar_payload(data_aviso)

    elif texto == "0":
        enviar_menu_bienvenida(number)

    else:
        enviar_menu_bienvenida(number)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)