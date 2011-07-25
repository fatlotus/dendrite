from twisted.internet import reactor # FIXME

class ServerSideConnection():
	def send(self, *vargs, **dargs):
		self.protocol.sendPacket(*vargs, **dargs)
	
	def initialize_connection(self):
		self.send("echo")