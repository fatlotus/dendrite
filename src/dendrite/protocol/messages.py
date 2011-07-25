from twisted.internet import protocol
from dendrite.protocol import low_level

class DendriteServerFactory(protocol.ServerFactory):
	protocol = low_level.DendriteServerProtocol

class DendriteClientFactory(protocol.ClientFactory):
	protocol = low_level.DendriteClientProtocol