from twisted.internet import reactor # FIXME

class ServerSideConnection():
	def heartbeat(self):
		def handle_response(name, reply, cancel):
			cancel()
		self.send("echo", handle_response)
		
		reactor.callLater(1, self.heartbeat)
	
	def received_echo(self, reply):
		pass
	
	def initialize_connection(self):
		self.heartbeat()

class ClientSideConnection():
	def initialize_connection(self):
		pass
		
	def received_echo(self, reply):
		reply("echo")