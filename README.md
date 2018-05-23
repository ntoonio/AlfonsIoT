# Alfons IoT

This is a package for IoT's to interact with Alfons.

	import AlfonsIoT as iot

	def onMessage(client, userdata, msg):
		print(msg.topic + " " + str(msg.payload))

	iot.connect(on_connect=onConnect, on_message=onMessage)