from bottle import run, request, post, default_app
import paho.mqtt.client as mqtt
import threading


def mqttRun():
    client.connect("xxxxxxxxxx", 1883, 60)
    client.loop_forever()


client = mqtt.Client()
mqttThread = threading.Thread(target=mqttRun)


def on_connect(mqttclient, userdata, flags, rc):
    print("Connected with result code " + str(rc))


def on_message(mqttclient, userdata, msg):
    # print(msg.topic + " " + str(msg.payload))
    pass


@post('/send')
def send():
    body = request.json
    topic = "remoteControl/devices/{id}/code/{encoding}Controller".format(id=body['id'], encoding=body['encoding'])
    client.publish(topic, body['code'])


if __name__ == "__main__":
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set('xxxxxxxxx', 'xxxxxxxxx')
    mqttThread.start()
    run(host='127.0.0.1', port=8080, debug=True, reloader=True)
else:
    application = default_app()
