import socket
import json
import os
import string
import random
import time
import sys

import paho.mqtt.client
import yaml

_block = False
def block():
	"Block further execution. Ex useful when you only want to run a function when received a message. Can be unblocked by setting `_block` to `False`"
	_block = True
	while _block:
		time.sleep(1)

def _getIP():
	if "ip" in config:
		return config["ip"]

	discoverSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
	discoverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	discoverSocket.sendto(b"discover", ("255.255.255.255", 27369))
	
	return json.loads(discoverSocket.recv(1024))["ip"]

def _getID():
	if "id" in config:
		return config["id"]
	
	clientId = "".join(random.choices(string.ascii_letters + string.digits, k=16))
	config["id"] = clientId
	
	with open(PATH + "/config.yaml", "w") as f:
		yaml.dump(config, f, default_flow_style=False)

	return clientId

def connect(**kwargs):
	# MQTT
	onMessage = kwargs.get("on_message")
	if onMessage is not None:
		mqtt.on_message = onMessage
	
	onConnect = kwargs.get("on_connect")
	if onConnect is not None:
		mqtt.on_connect = onConnect

	mqtt.connect(_getIP(), 27370, 60)
	mqtt.loop_start()

PATH = os.path.dirname(os.path.abspath(sys.argv[0]))

with open(PATH + "/config.yaml") as f:
	config = yaml.load(f)

# MQTT
mqtt = paho.mqtt.client.Client()
mqtt._client_id = _getID()