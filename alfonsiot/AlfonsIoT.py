import socket
import json
import string
import time
import paho.mqtt.client as mqtt
import requests
import logging
import random
import ssl
import re

log = logging.getLogger("alfonsiot")

class AlfonsIoT():
	def __init__(self, host=None, port=None, **kwargs):
		self._host = host
		self._port = port

		self._username = kwargs.pop("username", None)
		self._password = kwargs.pop("password", None)

		self._clientID = kwargs.get("clientID", _createRandomString(10))
		log.debug("Alfons client ID is '{}'{}".format(self._clientID, ", which was newly generated" if kwargs.get("clientID") == None else ""))

		self._subscriptions = {}

		self.onConnect = None
		self.onMessage = None
		self.mqttOnDisconnect = None

		self._mqttTCPport = None

		self._sslEnable = kwargs.pop("ssl", False)

	def start(self):
		# If either host or port are known, try to auto-discover
		if self._host == None or self._port == None:
			discoData = _findAlfons()
			if not discoData: raise Exception("Couldn't find Alfons server") # TODO: Find a better exception
			self._sslEnable = discoData["ssl"]
			self._host = discoData["domain"] if self._sslEnable else discoData["ip"]
			self._port = discoData["web_port"]

		try:
			r = requests.get(self.webURL + "api/v1/info/")
		except requests.exceptions.SSLError as e: # In case both host and port was set at init, but ssl was set to wrong value
			raise Exception("Alfons is using SSL, this client is not")

		if not (r.status_code >= 200 and r.status_code < 300):
			log.debug("Tried getting api from base '{}'".format(self.webURL))
			raise requests.HTTPError("Getting info API failed")

		data = r.json()
		self._host = data["domain"] if data["ssl"] else data["ip"]
		self._mqttTCPPort = data["mqtt"]["tcp_port"]

		self._connectMQTT()

	def _connectMQTT(self):
		self._client = mqtt.Client(client_id=self._clientID, clean_session=True, protocol=mqtt.MQTTv311, transport="tcp")

		if self._username != None:
			self._client.username_pw_set(self._username, self._password)

		self._client.on_message = self._mqttOnMessage
		self._client.on_connect = self._mqttOnConnect
		self._client.on_disconnect = self._mqttOnDisconnect

		if self._sslEnable:
			sslContext = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
			sslContext.load_verify_locations(cafile=requests.certs.where())
			self._client.tls_set_context(sslContext)

		self._client.connect(self._host, self._mqttTCPPort)
		self._client.loop_start()

	def subscribe(self, topic, func, **kwargs):
		if not topic in self._subscriptions:
			self._subscriptions[topic] = {}

		subKey = _createRandomString(5)
		self._subscriptions[topic][subKey] = func
		self._client.subscribe(topic, kwargs.get("qos", 1))

		return subKey

	def unsubscribe(self, **kwargs):
		"Unsubscribe and remove the listener. Set `key` to remove the listener for that key, or set `topic` to remove all listeners for that topic"

		key = kwargs.pop("key")
		topic = kwargs.pop("topic")

		if key:
			for t in self._subscriptions:
				b = False
				for k in self._subscriptions[t]:
					if k == key:
						del self._subscriptions[t][k]
						topic = t

						b = True
						break
				if b: break
		elif topic:
			del self._subscriptions[topic]

		self._client.unsubscribe(topic)

		# If the topic is empty, remove it
		for t in self._subscriptions:
			if len(self._subscriptions[t]) == 0:
				del self._subscriptions[t]

	def publish(self, topic, payload, **kwargs):
		self._client.publish(topic, payload, **kwargs)

	def _mqttOnConnect(self, client, userData, flags, rc):
		log.info("MQTT connected. userData={} flags={} rc={}".format(userData, flags, rc))

		if self.onConnect is not None:
			self.onConnect(self)

	def _mqttOnMessage(self, client, userData, message):
		log.debug("_mqttOnMessage userData={} topic={} payload={}".format(userData, message.topic, message.payload.decode("utf-8")))

		for t in self._subscriptions:
			if _doTopicsMatch(t, message.topic):
				for key in self._subscriptions[t]:
					f = self._subscriptions[t][key]
					f(message.payload.decode("utf-8"))

		if self.onMessage is not None:
			self.onMessage(self, message.topic, message.payload.decode("utf-8"))

	def _mqttOnDisconnect(self, client, userData, rc):
		log.debug("_mqttOnDisconnect userData={} rc={}".format(userData, rc))

		if self.mqttOnDisconnect is not None:
			self.mqttOnDisconnect(client, userData, rc)

	@property
	def webURL(self):
		# Don't include the port if it's the protocol's default
		portStr = (":" + str(self._port) if self._sslEnable and self._port != 443 or not self._sslEnable and self._port != 80 else "")
		return "http{}://".format("s" if self._sslEnable else "") + self._host + portStr + "/"

def _createRandomString(length=10, letters=string.hexdigits):
	"Generate a random string"
	return "".join(random.choice(letters) for i in range(length))

def _doTopicsMatch(base, head):
	# For some reason hbmqtt thinks '+' and '#' are the same
	pattern = re.sub("((?<=(\\/))|(?<=^))(\\+|#)(?=(\\/|$))", ".*", base).replace("/", "\\/")
	return re.match(pattern, head) is not None

def _findAlfons(ip=None):
	discoverSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
	discoverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	discoverSocket.settimeout(1)

	startSearchTime = time.time()

	msg = None
	while not msg:
		ip = ip or "255.255.255.255"

		log.debug("Broadcasting alfons discover to {}:27369".format(ip))
		discoverSocket.sendto(b"discover", (ip, 27369))

		try:
			msg = discoverSocket.recv(1024)
		except socket.timeout:
			if startSearchTime + 30 < time.time(): raise socket.timeout()

	data = json.loads(msg.decode("utf-8"))
	return data

def start(**kwargs):
	a = AlfonsIoT(**kwargs)
	a.start()

	return a
