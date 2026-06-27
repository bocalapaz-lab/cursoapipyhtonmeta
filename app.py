from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import http.client
import json
import time

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
            tipo = mensaje.get("type")

            agregar_mensajes_log(json.dumps(mensaje, ensure_ascii=False))

            if tipo == "text":
                texto = mensaje["text"]["body"].strip()

                if texto == "1":
                    enviar_conocenos(numero)
                elif texto == "2":
                    enviar_video_construccion(numero)
                elif texto == "3":
                    enviar_ubicacion(numero)
                elif texto == "4":
                    enviar_estacionamiento(numero)
                elif texto == "5":
                    enviar_ayuda_personalizada(numero)
                else:
                    enviar_bienvenida(numero)

            elif tipo == "interactive":
                interactive = mensaje.get("interactive", {})
                if interactive.get("type") == "button_reply":
                    boton_id = interactive["button_reply"]["id"]

                    if boton_id == "btnmensaje":
                        enviar_confirmacion_mensaje(numero)
                    elif boton_id == "btnllamada":
                        enviar_confirmacion_llamada(numero)

            else:
                # Si mandan audio, imagen, sticker, etc. -> tambien mandamos la bienvenida
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
        "Authorization": "Bearer EAAVEa8dSzTcBRZCRz3dNQgIm11BsShisj3BmvbZAuBJ9sw3kUhsuS5Wi76BInOWhvdHZB2WKmpV5M2eA7IY0VNTMLTpRCULbdNZBI6gZCclGs5aZCSeTIh0mUoPzC20BcBPMmKeKvmwxiJtgvxlI6DQ2l2bAwnZAh13JEfUOdSLZCCH6kVTlqVmkZC8StGrRZAWkcMhSxYTdqZCRQG9u9u0KMFRfbv2BlEyfrVLMafzovv7jM2nZADC2ZCSvhzeHdBeiiq74hZAxF0iZBIbuEtA6pNzBZABuHqe27FYosVXxPvrHHQZDZD"
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

    # Pequena pausa para que la imagen alcance a procesarse/mostrarse
    # antes de que llegue el texto de bienvenida.
    time.sleep(1.5)

    # 2. Mensaje de bienvenida + menu
    data_bienvenida = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": (
                "¡Hola! 👋 Gracias por escribirnos a *BOCA*.\n\n"
                "Soy el asistente virtual del consultorio. Estoy aquí para "
                "ayudarte en lo que necesites. 😊\n\n"
                "Elige una opción escribiendo el número:\n\n"
                "1️⃣ Conócenos\n"
                "2️⃣ Video de nosotros\n"
                "3️⃣ Ubicación del consultorio\n"
                "4️⃣ Estacionamiento\n"
                "5️⃣ Ayuda personalizada\n\n"
                "Escribe el número de la opción que te interese."
            )
        }
    }
    enviar_payload(data_bienvenida)

def enviar_conocenos(number):
    number = normalizar_numero_mx(number)

    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": (
                "👋 *Conócenos*\n\n"
                "En *BOCA* contamos con un equipo especializado, comprometido "
                "con tu salud y bienestar:\n\n"
                "🦷 *Dra. Yaxcy Reyes García*\n"
                "Especialista en Cirugía Maxilofacial\n\n"
                "🦷 *Dr. Rubén Fernández Tamayo*\n"
                "Especialista en Cirugía Maxilofacial\n\n"
                "🎯 *Misión*\n"
                "Brindar atención odontológica y maxilofacial de excelencia, "
                "con un enfoque humano y profesional, utilizando técnicas "
                "actualizadas para mejorar la salud y calidad de vida de "
                "nuestros pacientes.\n\n"
                "🔭 *Visión*\n"
                "Ser un consultorio de referencia en cirugía maxilofacial, "
                "reconocido por la confianza de nuestros pacientes, la "
                "calidez de nuestro trato y la calidad de nuestros resultados.\n\n"
                "Escribe *0* para volver al menú principal. 😊"
            )
        }
    }
    enviar_payload(data)

def enviar_video_construccion(number):
    number = normalizar_numero_mx(number)

    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": (
                "🚧 *Video en construcción*\n\n"
                "Estamos preparando con mucho cariño un video para darte la "
                "bienvenida que te mereces y mostrarte nuestras instalaciones. "
                "Estará disponible muy pronto. ¡Gracias por tu paciencia! 😊\n\n"
                "Escribe *0* para volver al menú principal."
            )
        }
    }
    enviar_payload(data)

def enviar_ubicacion(number):
    number = normalizar_numero_mx(number)

    # 1. Mandamos el pin de ubicacion
    data_ubicacion = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "location",
        "location": {
            "latitude": "19.056722627267366",
            "longitude": "-98.23117504866542",
            "name": "BOCA",
            "address": "Av. Rosendo Márquez 16, 50 Doctors Torres Médicas V, La Paz, 72160 Heroica Puebla de Zaragoza, Pue."
        }
    }
    enviar_payload(data_ubicacion)

    time.sleep(1.5)

    # 2. Mensaje de seguimiento con la direccion en texto + opcion de volver al menu
    data_texto = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": (
                "📍 *Nuestra ubicación*\n\n"
                "Av. Rosendo Márquez 16, 50 Doctors Torres Médicas V\n"
                "La Paz, 72160 Heroica Puebla de Zaragoza, Pue.\n\n"
                "¡Te esperamos! 😊\n\n"
                "Escribe *0* para volver al menú principal."
            )
        }
    }
    enviar_payload(data_texto)

def enviar_estacionamiento(number):
    number = normalizar_numero_mx(number)

    # 1. Mandamos el pin de ubicacion del estacionamiento
    data_ubicacion = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "location",
        "location": {
            "latitude": "19.057766",
            "longitude": "-98.231919",
            "name": "Estacionamiento",
            "address": "La Paz, 72160 Heroica Puebla de Zaragoza, Pue."
        }
    }
    enviar_payload(data_ubicacion)

    time.sleep(1.5)

    # 2. Aclaracion + descargo de responsabilidad
    data_texto = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": (
                "🅿️ *Estacionamiento*\n\n"
                "Como medida de comodidad para ti, te compartimos la "
                "ubicación de un estacionamiento cercano, justo cruzando "
                "la calle (ubicación enviada arriba 👆).\n\n"
                "ℹ️ Este estacionamiento es independiente y *no pertenece "
                "ni al hospital ni a nuestro consultorio BOCA*. Es un "
                "servicio externo que se encuentra cerca para tu comodidad.\n\n"
                "⚠️ Por lo anterior, *BOCA no se hace responsable* por tu "
                "vehículo, sus pertenencias, ni por cualquier situación que "
                "pudiera presentarse en dicho estacionamiento.\n\n"
                "Escribe *0* para volver al menú principal. 😊"
            )
        }
    }
    enviar_payload(data_texto)

def enviar_ayuda_personalizada(number):
    number = normalizar_numero_mx(number)

    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": (
                    "💬 *Ayuda personalizada*\n\n"
                    "Cuéntanos qué necesitas y con gusto te ayudamos. Elige "
                    "la opción que se ajuste mejor a tu situación:\n\n"
                    "Si se trata de una urgencia médica grave, te "
                    "recomendamos acudir directamente a un servicio de "
                    "urgencias o llamar al 911."
                )
            },
            "footer": {
                "text": "Selecciona una opción"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "btnmensaje",
                            "title": "Dejar mi mensaje"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "btnllamada",
                            "title": "Solicitar llamada"
                        }
                    }
                ]
            }
        }
    }
    enviar_payload(data)

def enviar_confirmacion_mensaje(number):
    number = normalizar_numero_mx(number)

    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": (
                "🙏 *¡Gracias por escribirnos!*\n\n"
                "Tu mensaje ha quedado registrado en nuestro sistema y será "
                "leído por uno de nuestros especialistas a la brevedad "
                "posible.\n\n"
                "Hacemos nuestro mejor esfuerzo por responder en el menor "
                "tiempo posible; sin embargo, el tiempo de respuesta puede "
                "variar dependiendo de nuestra agenda y horario de atención.\n\n"
                "Agradecemos mucho tu paciencia y confianza en *BOCA*. 😊\n\n"
                "Escribe *0* para volver al menú principal."
            )
        }
    }
    enviar_payload(data)

def enviar_confirmacion_llamada(number):
    number = normalizar_numero_mx(number)

    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": (
                "📞 *Solicitud de llamada recibida*\n\n"
                "Hemos registrado tu solicitud y uno de nuestros "
                "especialistas se pondrá en contacto contigo por teléfono "
                "lo antes posible.\n\n"
                "Te pedimos estar al pendiente de tu teléfono, ya que la "
                "llamada podría llegar desde un número distinto al de este "
                "chat.\n\n"
                "Gracias por confiar en *BOCA* para tu atención. 😊\n\n"
                "Escribe *0* para volver al menú principal."
            )
        }
    }
    enviar_payload(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)