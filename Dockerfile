FROM python:3
ADD . /
RUN pip3 install bottle flask paho-mqtt
CMD [ "python", "./main.py" ]
