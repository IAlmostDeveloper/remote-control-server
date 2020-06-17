import time

from bottle import run, request, response, post, get, default_app, HTTPResponse
import paho.mqtt.client as mqtt
import threading
import json
from database import DatabaseManager
from mqttclient import on_disconnect, on_connect, on_message, on_publish
from connections import mqtt_address, mqtt_port, mqtt_username, mqtt_password
import secrets
import re

client = mqtt.Client()

sessionTokens = []


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
            client.publish("remoteControl/devices/{id}/code/{encoding}Controller"
                           .format(id=command['id'], encoding=command['encoding']), json.dumps(command['code']))
            time.sleep(int(command['delay'])/1000)


mqttThread = threading.Thread(target=mqttRun)


def registerUser(login, password):
    if len(DatabaseManager.checkUser(login)) != 0:
        return False
    DatabaseManager.addUser(login, password)
    return True


def authorizeUser(login, password):
    if len(DatabaseManager.getUser(login, password)) != 0:
        token = secrets.token_hex(20)
        sessionTokens.append(token)
        return token
    else:
        return 0


@get('/')
def index():
    client.publish('hello', 'hello world')
    return 'Hello world'


@post('/send')
def send():
    body = request.json
    topic = "remoteControl/devices/{id}/code/{encoding}Controller".format(id=body['id'], encoding=body['encoding'])
    client.publish(topic, body['code'])


@post('/register')
def register():
    body = request.json
    registered = registerUser(body['login'], body['password'])
    _response = {'error': '' if registered else 'User already registered'}
    return HTTPResponse(status=200, body=json.dumps(_response))


@post('/auth')
def auth():
    body = request.json
    token = authorizeUser(body['login'], body['password'])
    _response = {'error': '' if token != 0 else 'Incorrect user data', 'token': token}
    return HTTPResponse(status=200, body=json.dumps(_response))


@post('/script')
def addScript():
    body = request.json
    # if not sessionTokens.__contains__(body['token']):
    #     return HTTPResponse(status=401)
    split = re.split(';', body['sequence'])
    isValid = len(split) >= 5 and len(split) % 5 == 0
    if isValid:
        DatabaseManager.addScript(body['name'], body['userId'], body['sequence'])
    _response = {'parsed': split, 'valid': isValid, 'error': '' if isValid else 'Invalid sequence'}
    return HTTPResponse(status=200, body=json.dumps(_response))


@post('/execute')
def executeScript():
    body = request.json
    sequence = DatabaseManager.getScript(body['id'])
    split = re.split(';', sequence[0])
    commands = []
    for i in range(0, len(split), 5):
        command = {'id': split[i], 'code': split[i + 1], 'encoding': split[i + 2], 'count': split[i + 3],
                   'delay': split[i + 4]}
        commands.append(command)
    scriptThread = threading.Thread(target=sendSequence, args=[commands])
    scriptThread.start()
    _response = {"sequence": sequence, "commands": commands}
    return HTTPResponse(status=200, body=json.dumps(_response))


@post('/smartthings')
def smartthings():
    f = open('log.txt', 'a')
    body = request.json
    print('--------------------------------------------')
    print(body)
    print('--------------------------------------------')
    if body['lifecycle'] == 'CONFIGURATION':
        phase = body['configurationData']['phase']
        if phase == 'INITIALIZE':
            response.add_header('content-type', 'application/json')
            return HTTPResponse(status=200, body="""{
      "configurationData": {
        "initialize": {
          "name": "Remote Control",
          "description": "Remote Control",
          "id": "app",
          "permissions": ["r:rules:*", "w:rules:*" ],
          "firstPageId": "1"
        }
      }
    }""")
        if phase == 'PAGE':
            response.add_header('content-type', 'application/json')
            return HTTPResponse(status=200, body="""{
      "configurationData": {
        "page": {
          "pageId": "1",
          "name": "Remote Control",
          "nextPageId": null,
          "previousPageId": null,
          "complete": true,
          "sections": [
            {
              "name": "Remote Control",
              "settings": [
              ]
            }
          ]
        }
      }
    }""")
    if body['lifecycle'] == 'INSTALL':
        return HTTPResponse(status=200, body="""{
        "installData" : {}
        }""")
    if body['lifecycle'] == 'UPDATE':
        return HTTPResponse(status=200, body="""{
        "updateData" : {}
        }""")

    # log = str(datetime.datetime.now()) + ' POST /send ' + str(response.status_code) + '\n'
    # log += 'Id: ' + str(body['id']) + '\n' + 'Code: ' + body['code'] + '\n' + 'Encoding: ' + body['encoding'] + '\n'
    # print(log, file=f)
    # print(log)
    # topic = "remoteControl/devices/{id}/code/{encoding}Controller".format(id=body['id'], encoding=body['encoding'])
    # client.publish(topic, body['code'])
    # print('Topic: ' + topic + ' Code: ' + body['code'], file=f)
    # print('Topic: ' + topic + ' Code: ' + body['code'])


mqttThread.start()
DatabaseManager.createTables()
if __name__ == "__main__":
    run(host='127.0.0.1', port=50200, debug=True, reloader=True)
else:
    application = default_app()
