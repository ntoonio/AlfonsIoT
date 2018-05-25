import socket
import json
import os
import string
import random
import time
import sys

import paho.mqtt.client
import yaml

projectPath = ""
config = {"uninitialized": True}
mqtt = paho.mqtt.client.Client()

def _getIP():
	ip = getConfig("ip")
	if ip: return ip

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
	clientId = getConfig("id")
	if clientId: return clientId
	
	clientId = "".join(random.choices(string.ascii_letters + string.digits, k=16))
	data["id"] = clientId

	with open(projectPath + "/data.json", "w") as f:
		json.dump(data, f)

	return clientId

def getConfig(key):
	if key in config:
		return config[key]

	if key in data:
		return data[key]
	
	return None

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

def setup(path = None):
	"Path to a config file"
	
	global mqtt, config, data, projectPath

	if path == None:
		configPath = os.path.abspath(sys.argv[0])
	else:
		configPath = path
	
	projectPath = os.path.dirname(configPath)
	
	# Read files
	try:
		with open(configPath) as f:
			config = yaml.load(f)
	except:
		config = {}
	
	try:
		with open(projectPath + "/data.json") as f:
			data = json.load(f)
	except:
		data = {}

	# MQTT
	mqtt._client_id = _getID()