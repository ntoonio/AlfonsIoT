import socket
import json
import string
import time
import paho.mqtt.client as mqtt
import requests
import logging
import random
import ssl

class AlfonsIoT():
	def __init__(self, host=None, port="27370", **kwargs):
		self._host = host
		self._port = port

		self._username = kwargs.pop("username", None)
		self._password = kwargs.pop("password", None)

		self._kwargs = kwargs

		self.mqttOnConnect = None
		self.mqttOnMessage = None
		self.mqttOnDisconnect = None

		self._sslEnable = kwargs.pop("ssl", True)

	def start(self):
		if self._host == None or self._port == None:
			self._findAlfons()
			if not self.discoveryData: raise Exception("Couldn't find Alfons server")

		self.webURL = "http{}://".format("s" if self._sslEnable else "") + self._host + ":" + str(self._port) + "/"

		r = requests.get(self.webURL + "api/v1/info/")
		if not (r.status_code >= 200 and r.status_code < 300):
			raise requests.HTTPError("Getting info API failed")

		data = r.json()
		self._host = data["domain"] if data["ssl"] else data["ip"]
		self._port = data["web_port"]
		self._data = data

		self._connectMQTT()

	def _findAlfons(self):
		discoverSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
		discoverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		discoverSocket.settimeout(1)

		startSearchTime = time.time()

		msg = None
		while not msg:
			ip = self._host or "255.255.255.255"

			logging.debug("Broadcasting alfons discover to {}:27369".format(ip))
			discoverSocket.sendto(b"discover", (ip, 27369))

			try:
				msg = discoverSocket.recv(1024)
			except socket.timeout:
				if startSearchTime + 30 < time.time(): raise socket.timeout()

		data = json.loads(msg.decode("utf-8"))

		self._host = data["domain"] if data["ssl"] else data["ip"]
		self._port = data["web_port"]
		self.discoveryData = data

	def _connectMQTT(self):
		clientID = self._kwargs.get("clientID", _createRandomString(10))

		self._client = mqtt.Client(clientID, transport="tcp")

		if self._username != None:
			self._client.username_pw_set(self._username, self._password)

		self._client.on_message = self._mqttOnMessage
		self._client.on_connect = self._mqttOnConnect
		self._client.on_disconnect = self._mqttOnDisconnect

		sslContext = None
		if self._sslEnable:
			sslContext = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
			sslContext.load_verify_locations(cafile=requests.certs.where())

		self._client.tls_set_context(sslContext)
		self._client.connect(self._host, self._data["mqtt"]["tcp_port"])
		self._client.loop_start()

	def _mqttOnConnect(self, *args, **kwargs):
		print("_mqttOnConnect", args, kwargs)
		try:
			self.mqttOnConnect(*args, **kwargs)
		except TypeError:
			pass

	def _mqttOnMessage(self, *args, **kwargs):
		print("_mqttOnMessage", args, kwargs)
		try:
			self.mqttOnMessage(*args, **kwargs)
		except TypeError:
			pass

	def _mqttOnDisconnect(self, *args, **kwargs):
		print("_mqttOnDisconnect", args, kwargs)
		try:
			self.mqttOnConnect(*args, **kwargs)
		except TypeError:
			pass

def _createRandomString(length=10, letters=string.hexdigits):
    "Generate a random string"
    return "".join(random.choice(letters) for i in range(length))

def start(**kwargs):
	a = AlfonsIoT(**kwargs)
	a.start()

	return a
