# Alfons IoT

This is a package for IoT's to interact with Alfons.

	import alfonsiot

	def onMessage(iot, topic, payload):
		print("onMessage", topic, payload)

	def onTopicMessage(message):
		print("Got message from specified", message)

	def onConnect(iot):
		print("Connected!", iot)

		iot.subscribe("topic", onTopicMessage)

		iot.publish("topic", "Message!")

	iot = alfonsiot.start(host="", port="", username="", password="")

	iot.onConnect = onConnect
	iot.onMessage = onMessage
