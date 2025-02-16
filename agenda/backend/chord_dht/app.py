from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from storage import Database  # Asegúrate de que 'database.py' contenga el código que compartiste
import os

app = Flask(__name__, template_folder='../../../frontend/templates', static_folder='../../../backend/staticfiles')
CORS(app)  # Esto permite que el frontend (posiblemente en otro dominio) pueda comunicarse

# Crea una instancia global de la clase Database
db = Database()

# Cargar la página principal sin hacer operaciones en la base de datos
@app.route("/")
def index():
    return render_template("index.html")

# Cargar la página principal sin hacer operaciones en la base de datos
@app.route("/register/")
def register():
    return render_template("register.html")

@app.route("/login/")
def login():
    return render_template("login.html")

@app.route("/forgot/")
def forgot():
    return render_template("forgot.html")

# Ruta para servir archivos estáticos (JS y CSS)
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(os.path.join(app.static_folder), filename)


# ----------------------------
# Endpoints para Usuarios
# ----------------------------

# Endpoint para registrar usuario
@app.route('/sign_up/', methods=['POST'])
def sign_up():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    if db.register_user(username, email, password):
        return jsonify({'message': 'Usuario registrado exitosamente'}), 201
    else:
        return jsonify({'message': 'Error al registrar el usuario (posible email duplicado)'}), 400

# Endpoint para iniciar sesión
@app.route('/log_in/', methods=['POST'])
def log_in():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = db.login_user(username, password)
    if user:
        return jsonify({'user': user}), 200
    else:
        return jsonify({'message': 'Credenciales incorrectas'}), 401

# ----------------------------
# Endpoints para Contactos
# ----------------------------

# Endpoint para agregar un contacto
@app.route('/contacts/', methods=['POST'])
def add_contact():
    data = request.get_json()
    user_id = data.get('user_id')
    contact_name = data.get('contact_name')
    owner_id = data.get('owner_id')
    if db.add_contact(user_id, contact_name, owner_id):
        return jsonify({'message': 'Contacto agregado'}), 201
    else:
        return jsonify({'message': 'Error al agregar el contacto'}), 400

# Endpoint para listar contactos
@app.route('/contacts/<int:user_id>', methods=['GET'])
def list_contacts(user_id):
    print("user_id", user_id)
    contacts = db.list_contacts(user_id)
    print("contacts:", contacts)
    return jsonify({'contacts': contacts}), 200

# Endpoint para obtener id a partir de username
@app.route('/contacts/get_user_id/', methods=['POST'])
def getUserID():
    data = request.get_json()
    contact = db.getUserID(data.get('username'))
    if contact:
        return jsonify({"contact": contact}), 200
    else:
        return jsonify({'message': 'Credenciales incorrectas'}), 401

# ----------------------------
# Endpoints para Eventos
# ----------------------------

@app.route('/create_event/', methods=['POST'])
def create_event():
    data = request.get_json()
    name = data.get('title')
    date = data.get('start_time').split("T")[0]  # Formato: 'YYYY-MM-DD'
    owner_id = data.get('owner_id')
    privacy = data.get('privacy')
    group_id = data.get('group', None)
    if db.create_event(name, date, owner_id, privacy, group_id):
        return jsonify({'message': 'Evento creado exitosamente'}), 201
    else:
        return jsonify({'message': 'Error al crear el evento'}), 400

@app.route('/create_group_event/', methods=['POST'])
def create_group_event():
    data = request.get_json()
    name = data.get('name')
    date = data.get('date')
    owner_id = data.get('owner_id')
    group_id = data.get('group_id')
    if db.create_group_event(name, date, owner_id, group_id):
        return jsonify({'message': 'Evento grupal creado exitosamente'}), 201
    else:
        return jsonify({'message': 'Error al crear el evento grupal'}), 400

@app.route('/create_individual_event/', methods=['POST'])
def create_individual_event():
    data = request.get_json()
    name = data.get('name')
    date = data.get('date')
    owner_id = data.get('owner_id')
    contact_id = data.get('contact_id')
    if db.create_individual_event(name, date, owner_id, contact_id):
        return jsonify({'message': 'Evento individual creado exitosamente'}), 201
    else:
        return jsonify({'message': 'Error al crear el evento individual'}), 400

@app.route('/confirm_event/<int:event_id>/', methods=['POST'])
def confirm_event(event_id):
    if db.confirm_event(event_id):
        return jsonify({'message': 'Evento confirmado exitosamente'}), 200
    else:
        return jsonify({'message': 'Error al confirmar el evento'}), 400

@app.route('/cancel_event/<int:event_id>/', methods=['POST'])
def cancel_event(event_id):
    if db.cancel_event(event_id):
        return jsonify({'message': 'Evento cancelado exitosamente'}), 200
    else:
        return jsonify({'message': 'Error al cancelar el evento'}), 400

@app.route('/list_events/<int:user_id>/', methods=['GET'])
def list_events(user_id):
    events = db.list_events(user_id)
    events_list = []
    for event in events:
        events_list.append({
            'id': event.id,
            'name': event.name,
            'date': event.date.strftime('%Y-%m-%d'),
            'owner_id': event.owner_id,
            'privacy': event.privacy,
            'group_id': event.group_id,
            'status': event.status
        })
    return jsonify({'events': events_list}), 200

@app.route('/list_events_pending/<int:user_id>/', methods=['GET'])
def list_events_pending(user_id):
    events = db.list_events_pending(user_id)
    events_list = []
    for event in events:
        events_list.append({
            'id': event.id,
            'name': event.name,
            'date': event.date.strftime('%Y-%m-%d'),
            'owner_id': event.owner_id,
            'privacy': event.privacy,
            'group_id': event.group_id,
            'status': event.status
        })
    return jsonify({'events': events_list}), 200

# ----------------------------
# Endpoints para Grupos
# ----------------------------

@app.route('/create_group/', methods=['POST'])
def create_group():
    data = request.get_json()
    name = data.get('name')
    owner_id = data.get('owner_id')
    if db.create_group(name, owner_id):
        return jsonify({'message': 'Grupo creado exitosamente'}), 201
    else:
        return jsonify({'message': 'Error al crear el grupo'}), 400

@app.route('/add_member_to_group/', methods=['POST'])
def add_member_to_group():
    data = request.get_json()
    group_id = data.get('group_id')
    user_id = data.get('user_id')
    role = data.get('role', 'member')
    if db.add_member_to_group(group_id, user_id, role):
        return jsonify({'message': 'Miembro agregado al grupo'}), 201
    else:
        return jsonify({'message': 'Error al agregar miembro al grupo'}), 400

@app.route('/remove_member_from_group/', methods=['POST'])
def remove_member_from_group():
    data = request.get_json()
    group_id = data.get('group_id')
    user_id = data.get('user_id')
    if db.remove_member_from_group(group_id, user_id):
        return jsonify({'message': 'Miembro eliminado del grupo'}), 200
    else:
        return jsonify({'message': 'Error al eliminar miembro del grupo'}), 400

@app.route('/list_groups/<int:user_id>/', methods=['GET'])
def list_groups(user_id):
    groups = db.list_groups(user_id)
    groups_list = [{'id': g[0], 'name': g[1]} for g in groups]
    return jsonify({'groups': groups_list}), 200

@app.route('/list_members/<int:group_id>/', methods=['GET'])
def list_members(group_id):
    members = db.list_members(group_id)
    return jsonify({'members': members}), 200

# ----------------------------
# Ejecutar la aplicación
# ----------------------------

if __name__ == '__main__':
    app.run(debug=True)


#! ########################################
# Eliminar grupo
# Eliminar contacto
# Abandonar grupo
# Agendas
# ---otros---
# test_token
#! ########################################