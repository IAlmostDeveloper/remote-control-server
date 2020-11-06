import json
import re
import secrets
import threading
import time

import paho.mqtt.client as mqtt
from bottle import run, request, post, get, default_app, HTTPResponse

from connections import mqtt_address, mqtt_port, mqtt_username, mqtt_password
from database import DatabaseManager
from mqttclient import on_disconnect, on_connect, on_message, on_publish

client = mqtt.Client()


def mqtt_run():
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_publish = on_publish
    client.username_pw_set(mqtt_username, mqtt_password)
    client.connect(mqtt_address, mqtt_port, 60)
    client.loop_forever()


def send_sequence(commands):
    print('executing script')
    for command in commands:
        for i in range(0, int(command['count'])):
            client.publish("remoteControl/devices/{id}/code/{encoding}"
                           .format(id=command['id'], encoding=command['encoding']), command['code'])
            time.sleep(int(command['delay']) / 1000)


mqtt_thread = threading.Thread(target=mqtt_run)


def register_user(login, password):
    if len(DatabaseManager.check_user(login)) != 0:
        return False
    DatabaseManager.add_user(login, password)
    return True


def authorize_user(login, password):
    if len(DatabaseManager.get_user(login, password)) != 0:
        token = secrets.token_hex(20)
        DatabaseManager.add_session(login, token)
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
    if not DatabaseManager.check_session(token):
        return HTTPResponse(status=401)
    user_id = DatabaseManager.get_user_id(request.query['user'])
    result = DatabaseManager.get_user_controllers(user_id)
    _response = {"controllers": [dict(x) for x in result]}
    return HTTPResponse(status=200, body=json.dumps(_response))


@post('/add/controller')
def add_controller():
    body = request.json
    token = body['token']
    if not DatabaseManager.check_session(token):
        return HTTPResponse(status=401)
    name = body['name']
    user_id = DatabaseManager.get_user_id(body['user'])
    controller_id = body['controller_id']
    encoding = body['encoding']
    buttons = body['buttons']
    _response = {'error': DatabaseManager.add_controller(name, user_id, controller_id, encoding, buttons)}
    return HTTPResponse(status=200, body=json.dumps(_response))


@post('/update/controller')
def update_controller():
    body = request.json
    token = body['token']
    if not DatabaseManager.check_session(token):
        return HTTPResponse(status=401)
    name = body['name']
    user_id = DatabaseManager.get_user_id(body['user'])
    buttons = body['buttons']
    _response = {'error': DatabaseManager.update_controller(name, user_id, buttons)}
    return HTTPResponse(status=200, body=json.dumps(_response))


@post('/delete/controller')
def delete_controller():
    body = request.json
    token = body['token']
    if not DatabaseManager.check_session(token):
        return HTTPResponse(status=401)
    name = body['name']
    user_id = DatabaseManager.get_user_id(body['user'])
    _response = {'error': DatabaseManager.delete_controller(name, user_id)}
    return HTTPResponse(status=200, body=json.dumps(_response))


@post('/send')
def send():
    body = request.json
    token = body['token']
    if not DatabaseManager.check_session(token):
        return HTTPResponse(status=401)
    topic = "remoteControl/devices/{id}/code/{encoding}".format(id=body['id'], encoding=body['encoding'])
    client.publish(topic, body['code'])
    return HTTPResponse(status=200)


@post('/receive')
def receive_code():
    body = request.json
    request_topic = body['request_topic']
    response_topic = body['response_topic']
    client.subscribe(response_topic)
    client.publish(request_topic, response_topic)
    key = secrets.token_hex(20)

    def add_code_to_db(mqttclient, userdata, msg):
        print('code received')
        code = json.loads(msg.payload.decode())['code']
        print(code)
        DatabaseManager.add_received_code(key, str(code))

    client.on_message = add_code_to_db
    _response = {'key': key}
    return HTTPResponse(status=200, body=json.dumps(_response))


@get('/receivedcode')
def get_received_code():
    token = request.query['token']
    if not DatabaseManager.check_session(token):
        return HTTPResponse(status=401)
    key = request.query['key']
    code = DatabaseManager.get_received_code(key)
    _response = {'code': code}
    return HTTPResponse(status=200, body=_response)


@post('/register')
def register():
    body = request.json
    registered = register_user(body['login'], body['password'])
    _response = {'error': '' if registered else 'User already registered'}
    return HTTPResponse(status=200, body=json.dumps(_response))


@post('/auth')
def auth():
    body = request.json
    print(body)
    token = authorize_user(body['login'], body['password'])
    _response = {'error': '' if token != "0" else 'Incorrect user data', 'token': token}
    return HTTPResponse(status=200, body=json.dumps(_response))


@get('/userscripts')
def user_scripts():
    token = request.query['token']
    if not DatabaseManager.check_session(token):
        return HTTPResponse(status=401)
    user_id = DatabaseManager.get_user_id(request.query['user'])
    _response = {'scripts': [dict(x) for x in DatabaseManager.get_user_scripts(user_id)]}
    return HTTPResponse(status=200, body=json.dumps(_response))


@post('/script')
def add_script():
    body = request.json
    token = body['token']
    if not DatabaseManager.check_session(token):
        return HTTPResponse(status=401)
    split = re.split(';', body['sequence'])
    is_valid = len(split) >= 5 and len(split) % 5 == 0
    error = ''
    if is_valid:
        user_id = DatabaseManager.get_user_id(body['user'])
        if user_id != -1:
            DatabaseManager.add_script(body['name'], user_id, body['sequence'])
        else:
            error = 'User does not exists'
    else:
        error = 'Invalid sequence'
    _response = {'parsed': split, 'valid': is_valid, 'error': error}
    return HTTPResponse(status=200, body=json.dumps(_response))


@post('/delete/script')
def delete_script():
    body = request.json
    token = body['token']
    if not DatabaseManager.check_session(token):
        return HTTPResponse(status=401)
    user_id = DatabaseManager.get_user_id(body['user'])
    DatabaseManager.delete_script(user_id, body['name'])
    return HTTPResponse(status=200)


@post('/execute')
def execute_script():
    body = request.json
    token = body['token']
    if not DatabaseManager.check_session(token):
        return HTTPResponse(status=401)
    sequence = DatabaseManager.get_script(body['id'])
    commands = []
    if len(sequence) != 0:
        split = re.split(';', sequence[0])
        for i in range(0, len(split), 5):
            command = {'id': split[i], 'code': split[i + 1], 'encoding': split[i + 2], 'count': split[i + 3],
                       'delay': split[i + 4]}
            commands.append(command)
    script_thread = threading.Thread(target=send_sequence, args=[commands])
    script_thread.start()
    return HTTPResponse(status=200)


mqtt_thread.start()
DatabaseManager.create_tables()
if __name__ == "__main__":
    run(host='0.0.0.0', port=8080, debug=True, reloader=True)
else:
    application = default_app()
