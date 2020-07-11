import time
import paho.mqtt.client as mqtt
import threading
import json
from database import DatabaseManager
from mqttclient import on_disconnect, on_connect, on_message, on_publish
from connections import mqtt_address, mqtt_port, mqtt_username, mqtt_password
import secrets
import re
from flask import Flask, request, jsonify, abort
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

client = mqtt.Client()


@app.errorhandler(403)
def resource_not_found(e):
    return jsonify(error=str(e)), 403


@app.errorhandler(401)
def resource_not_found(e):
    return jsonify(error=str(e)), 401


def mqttRun():
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_publish = on_publish
    client.username_pw_set(mqtt_username, mqtt_password)
    client.connect(mqtt_address, mqtt_port, 60)
    client.loop_forever()


def sendSequence(commands):
    print('executing script')
    for command in commands:
        for i in range(0, int(command['count'])):
            client.publish("remoteControl/devices/{id}/code/{encoding}"
                           .format(id=command['id'], encoding=command['encoding']), command['code'])
            time.sleep(int(command['delay']) / 1000)


mqttThread = threading.Thread(target=mqttRun)


def registerUser(login, password):
    if len(DatabaseManager.checkUser(login)) != 0:
        return False
    DatabaseManager.addUser(login, password)
    return True


def authorizeUser(login, password):
    if len(DatabaseManager.getUser(login, password)) != 0:
        token = secrets.token_hex(20)
        DatabaseManager.addSession(login, token)
        return token
    else:
        return "0"


@app.route('/')
def index():
    client.publish('hello', 'hello world')
    return 'Hello world'


@app.route('/controllers')
def controllers():
    token = request.args.get('token')
    if not DatabaseManager.checkSession(token):
        abort(401, description="Access denied")
    userId = DatabaseManager.getUserId(request.args.get('user'))
    result = DatabaseManager.getUserControllers(userId)
    _response = {"controllers": [dict(x) for x in result]}
    return jsonify(_response)


@app.route('/add/controller', methods=['POST'])
def addController():
    body = request.get_json()
    token = body['token']
    if not DatabaseManager.checkSession(token):
        abort(401, description="Access denied")
    name = body['name']
    userId = DatabaseManager.getUserId(body['user'])
    controllerId = body['controllerId']
    encoding = body['encoding']
    buttons = body['buttons']
    _response = {'error': DatabaseManager.addController(name, userId, controllerId, encoding, buttons)}
    return json.dumps(_response)


@app.route('/update/controller', methods=['POST'])
def updateController():
    body = request.get_json()
    token = body['token']
    if not DatabaseManager.checkSession(token):
        abort(401, description="Access denied")
    name = body['name']
    userId = DatabaseManager.getUserId(body['user'])
    buttons = body['buttons']
    _response = {'error': DatabaseManager.updateController(name, userId, buttons)}
    return json.dumps(_response)


@app.route('/delete/controller', methods=['POST'])
def deleteController():
    body = request.get_json()
    token = body['token']
    if not DatabaseManager.checkSession(token):
        abort(401, description="Access denied")
    name = body['name']
    userId = DatabaseManager.getUserId(body['user'])
    _response = {'error': DatabaseManager.deleteController(name, userId)}
    return json.dumps(_response)


@app.route('/send', methods=['POST'])
def send():
    body = request.get_json()
    token = body['token']
    if not DatabaseManager.checkSession(token):
        abort(401, description="Access denied")
    topic = "remoteControl/devices/{id}/code/{encoding}".format(id=body['id'], encoding=body['encoding'])
    client.publish(topic, body['code'])
    return ""


@app.route('/receive', methods=['POST'])
def receiveCode():
    body = request.get_json()
    requestTopic = body['requestTopic']
    responseTopic = body['responseTopic']
    client.subscribe(responseTopic)
    client.publish(requestTopic, responseTopic)
    key = secrets.token_hex(20)

    def addCodeToDb(mqttclient, userdata, msg):
        print('code received')
        code = json.loads(msg.payload.decode())['code']
        print(code)
        DatabaseManager.addReceivedCode(key, str(code))

    client.on_message = addCodeToDb
    _response = {'key': key}
    return json.dumps(_response)


@app.route('/receivedcode')
def getReceivedCode():
    token = request.args.get('token')
    if not DatabaseManager.checkSession(token):
        abort(401, description="Access denied")
    key = request.args.get('key')
    code = DatabaseManager.getReceivedCode(key)
    _response = {'code': code}
    return _response


@app.route('/register', methods=['POST'])
def register():
    body = request.get_json()
    registered = registerUser(body['login'], body['password'])
    _response = {'error': '' if registered else 'User already registered'}
    return json.dumps(_response)


@app.route('/auth', methods=['POST'])
def auth():
    body = request.get_json()
    print(body)
    token = authorizeUser(body['login'], body['password'])
    _response = {'error': '' if token != "0" else 'Incorrect user data', 'token': token}
    return json.dumps(_response)


@app.route('/userscripts')
def userScripts():
    token = request.args.get('token')
    if not DatabaseManager.checkSession(token):
        abort(401, description="Access denied")
    userId = DatabaseManager.getUserId(request.arg.get('user'))
    _response = {'scripts': [dict(x) for x in DatabaseManager.getUserScripts(userId)]}
    return json.dumps(_response)


@app.route('/script', methods=['POST'])
def addScript():
    body = request.get_json()
    token = body['token']
    if not DatabaseManager.checkSession(token):
        abort(401, description="Access denied")
    split = re.split(';', body['sequence'])
    isValid = len(split) >= 5 and len(split) % 5 == 0
    error = ''
    if isValid:
        userId = DatabaseManager.getUserId(body['user'])
        if userId != -1:
            DatabaseManager.addScript(body['name'], userId, body['sequence'])
        else:
            error = 'User does not exists'
    else:
        error = 'Invalid sequence'
    _response = {'parsed': split, 'valid': isValid, 'error': error}
    return json.dumps(_response)


@app.route('/delete/script', methods=['POST'])
def deleteScript():
    body = request.get_json()
    token = body['token']
    if not DatabaseManager.checkSession(token):
        abort(401, description="Access denied")
    userId = DatabaseManager.getUserId(body['user'])
    DatabaseManager.deleteScript(userId, body['name'])


@app.route('/execute', methods=['POST'])
def executeScript():
    body = request.get_json()
    token = body['token']
    if not DatabaseManager.checkSession(token):
        abort(401, description="Access denied")
    sequence = DatabaseManager.getScript(body['id'])
    commands = []
    if len(sequence) != 0:
        split = re.split(';', sequence[0])
        for i in range(0, len(split), 5):
            command = {'id': split[i], 'code': split[i + 1], 'encoding': split[i + 2], 'count': split[i + 3],
                       'delay': split[i + 4]}
            commands.append(command)
    scriptThread = threading.Thread(target=sendSequence, args=[commands])
    scriptThread.start()
    return ""


# mqttThread.start()
DatabaseManager.createTables()

if __name__ == '__main__':
    app.run(debug=True, port=8080)
