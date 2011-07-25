from twisted.internet import protocol
from dendrite.protocol import low_level
from dendrite.protocol import high_level

class DendriteServerFactory(protocol.ServerFactory):
	connection = high_level.ServerSideConnection
	protocol = low_level.DendriteServerProtocol
	
	def buildProtocol(self, *address):
		protocol = self.protocol()
		protocol.factory = self
		protocol.connection = self.connection()
		protocol.connection.protocol = protocol
		return protocol

class DendriteClientFactory(protocol.ClientFactory):
	protocol = low_level.DendriteClientProtocol