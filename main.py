import time

from bottle import run, Bottle, request, response, post, get, default_app, HTTPResponse
import paho.mqtt.client as mqtt
import threading
import json
import bottle
from database import DatabaseManager
from mqttclient import on_disconnect, on_connect, on_message, on_publish
from connections import mqtt_address, mqtt_port, mqtt_username, mqtt_password
import secrets
import re
from truckpad.bottle.cors import CorsPlugin
# the decorator
def cors(func):
    def wrapper(*args, **kwargs):
        bottle.response.set_header("Access-Control-Allow-Origin", "*")
        bottle.response.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        bottle.response.set_header("Access-Control-Allow-Headers", "Origin, Content-Type")

        # skip the function if it is not needed
        if bottle.request.method == 'OPTIONS':
            return

        return func(*args, **kwargs)

    return wrapper


app = bottle.app()

client = mqtt.Client()


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


@get('/')
def index():
    client.publish('hello', 'hello world')
    return 'Hello world'


@get('/controllers')
def controllers():
    token = request.query['token']
    if not DatabaseManager.checkSession(token):
        return HTTPResponse(status=401)
    userId = DatabaseManager.getUserId(request.query['user'])
    result = DatabaseManager.getUserControllers(userId)
    _response = {"controllers": [dict(x) for x in result]}
    return HTTPResponse(status=200, body=json.dumps(_response))


@post('/add/controller')
def addController():
    body = request.json
    token = body['token']
    if not DatabaseManager.checkSession(token):
        return HTTPResponse(status=401)
    name = body['name']
    userId = DatabaseManager.getUserId(body['user'])
    controllerId = body['controllerId']
    encoding = body['encoding']
    buttons = body['buttons']
    _response = {'error': DatabaseManager.addController(name, userId, controllerId, encoding, buttons)}
    return HTTPResponse(status=200, body=json.dumps(_response))


@post('/update/controller')
def updateController():
    body = request.json
    token = body['token']
    if not DatabaseManager.checkSession(token):
        return HTTPResponse(status=401)
    name = body['name']
    userId = DatabaseManager.getUserId(body['user'])
    buttons = body['buttons']
    _response = {'error': DatabaseManager.updateController(name, userId, buttons)}
    return HTTPResponse(status=200, body=json.dumps(_response))


@post('/delete/controller')
def deleteController():
    body = request.json
    token = body['token']
    if not DatabaseManager.checkSession(token):
        return HTTPResponse(status=401)
    name = body['name']
    userId = DatabaseManager.getUserId(body['user'])
    _response = {'error': DatabaseManager.deleteController(name, userId)}
    return HTTPResponse(status=200, body=json.dumps(_response))


@post('/send')
def send():
    body = request.json
    token = body['token']
    if not DatabaseManager.checkSession(token):
        return HTTPResponse(status=401)
    topic = "remoteControl/devices/{id}/code/{encoding}".format(id=body['id'], encoding=body['encoding'])
    client.publish(topic, body['code'])
    return HTTPResponse(status=200)


@post('/receive')
def receiveCode():
    body = request.json
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
    return HTTPResponse(status=200, body=json.dumps(_response))


@get('/receivedcode')
def getReceivedCode():
    token = request.query['token']
    if not DatabaseManager.checkSession(token):
        return HTTPResponse(status=401)
    key = request.query['key']
    code = DatabaseManager.getReceivedCode(key)
    _response = {'code': code}
    return HTTPResponse(status=200, body=_response)


@cors
@app.post('/register')
def register():
    body = request.json
    registered = registerUser(body['login'], body['password'])
    _response = {'error': '' if registered else 'User already registered'}
    return HTTPResponse(status=200, body=json.dumps(_response))


@cors
@app.route('/auth', method=['POST', 'OPTIONS'])
def auth():
    # body = json.load(request.body
    body = request.json
    print(request.body.read().decode('UTF-8'))
    token = authorizeUser(body['login'], body['password'])
    _response = {'error': '' if token != "0" else 'Incorrect user data', 'token': token}
    # return HTTPResponse(status=200, body=json.dumps(_response))
    response.headers['Content-Type'] = 'application/json'
    return json.dumps(_response)


@get('/userscripts')
def userScripts():
    token = request.query['token']
    if not DatabaseManager.checkSession(token):
        return HTTPResponse(status=401)
    userId = DatabaseManager.getUserId(request.query['user'])
    _response = {'scripts': [dict(x) for x in DatabaseManager.getUserScripts(userId)]}
    return HTTPResponse(status=200, body=json.dumps(_response))


@post('/script')
def addScript():
    body = request.json
    token = body['token']
    if not DatabaseManager.checkSession(token):
        return HTTPResponse(status=401)
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
    return HTTPResponse(status=200, body=json.dumps(_response))


@post('/delete/script')
def deleteScript():
    body = request.json
    token = body['token']
    if not DatabaseManager.checkSession(token):
        return HTTPResponse(status=401)
    userId = DatabaseManager.getUserId(body['user'])
    DatabaseManager.deleteScript(userId, body['name'])
    return HTTPResponse(status=200)


@post('/execute')
def executeScript():
    body = request.json
    token = body['token']
    if not DatabaseManager.checkSession(token):
        return HTTPResponse(status=401)
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
    return HTTPResponse(status=200)


app.install(CorsPlugin(origins=['http://list.of.allowed.domains.com', 'https://another.domain.org']))
# mqttThread.start()
DatabaseManager.createTables()
run(app)
