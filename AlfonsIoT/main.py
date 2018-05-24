import socket
import json
import os
import string
import random
import time
import sys

import paho.mqtt.client
import yaml

def _getIP():
	if "ip" in config:
		return config["ip"]

	discoverSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
	discoverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	discoverSocket.settimeout(1)
	
	msg = None

	while not msg:
		discoverSocket.sendto(b"discover", ("255.255.255.255", 27369))
		
		try:
			msg = discoverSocket.recv(1024)
		except socket.timeout:
			pass
	
	return json.loads(msg.decode("utf-8"))["ip"]

def _getID():
	if "id" in config:
		return config["id"]

	if "id" in data:
		return data["id"]
	
	clientId = "".join(random.choices(string.ascii_letters + string.digits, k=16))
	data["id"] = clientId

	with open(PATH + "/data.json", "w") as f:
		json.dump(data, f)

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

	if kwargs.get("block", False):
		mqtt.loop_forever()
	else:
		mqtt.loop_start()

PATH = os.path.dirname(os.path.abspath(sys.argv[0]))

# Read files

try:
	with open(PATH + "/config.yaml") as f:
		config = yaml.load(f)
except:
	config = {}

try:
	with open(PATH + "/data.json") as f:
		data = json.load(f)
except:
	data = {}

# MQTT
mqtt = paho.mqtt.client.Client()
mqtt._client_id = _getID()