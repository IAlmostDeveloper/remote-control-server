def on_connect(mqttclient, userdata, flags, rc):
    f = open('log.txt', 'a')
    print("Connected with result code " + str(rc), file=f)
    print("Connected with result code " + str(rc))


def on_disconnect(client, userdata, rc):
    f = open('log.txt', 'a')
    print('Disconnected from mqtt', file=f)
    print('Disconnected from mqtt')


def on_message(mqttclient, userdata, msg):
    # print(msg.topic + " " + str(msg.payload))
    pass


def on_publish(client, userdata, mid):
    f = open('log.txt', 'a')
    print('Successful publish ', file=f)
    print('Successful publish ')