from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

app = Flask(__name__)

#Configurtación de la base de datos SQLITE
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metapython.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#Modelo de la tabla log
class Log(db.Model): 
    id=db.Column(db.Integer,primary_key=True)
    fecha_y_hora = db.Column(db.DateTime,default=datetime.utcnow)
    texto = db.Column(db.TEXT)

#Crear la tabla si no existe 
with app.app_context(): 
    db.create_all()

#Función para ordenar los registros por fecha y hora 
def ordenar_por_fecha_y_hora(registros):
    return sorted(registros, key=lambda x: x.fecha_y_hora, reverse=True)

@app.route('/')
def index():
    #Obtener todos los registros de la base de datos
    registros = Log.query.all()
    registros_ordenados = ordenar_por_fecha_y_hora(registros)
    return render_template('index.html',registros=registros_ordenados)

mensajes_log = []

#Función para agregar mensajes y guardar en la base de datos
def agregar_mensajes_log(texto): 
    mensajes_log.append(texto)

    #Guardar el mensaje en la base de datos
    nuevo_registro = Log(texto=texto)
    db.session.add(nuevo_registro)
    db.session.commit()

#Token de verificación para la configuración 
TOKEN_CESAR = "cesar"

@app.route('/webhook', methods=['GET','POST'])
def webhook():
    if request.method == 'GET': 
        challenge = verificar_token(request)
        return challenge
    elif request.method == 'POST':
        response = recibir_mensajes(request)
        return response

def verificar_token(req): 
    return 0

def recibir_mensajes(req): 
    return 0

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

