# remote-control-server
http server for remote control project

## REST API для проекта RemoteControl
Сервер с базой данных и mqtt брокером

### Запуск сервера через docker-compose:
Рекомендуется запускать, используя docker-compose. Он развернет все необходимое самостоятельно.
```
git clone https://github.com/IAlmostDeveloper/remote-control-server
docker-compose up
```

### Запуск сервера вручную
#### Зависимости для сервера:
- Python 3
- Bottle
- Paho-mqtt

Также необходимо в файле connections.py указать данные для подключения к вашему mqtt брокеру. 
Сборка вручную не предусматривает создания собственного mqtt брокера, как в случае с docker-compose.

#### Запуск:
```
python3 main.py
```
