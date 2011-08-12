from twisted.internet import protocol
from dendrite.protocol import low_level
from dendrite.protocol import high_level

class DendriteServerFactory(protocol.ServerFactory):
   connection = high_level.ServerSideConnection
   protocol = low_level.DendriteServerProtocol
   
   def __init__(self, configuration):
      self.configuration = configuration
   
   def buildProtocol(self, *address):
      protocol = self.protocol(
         is_logging_all_packets=self.configuration.get('log_packets', False))
      protocol.factory = self
      protocol.connection = self.connection(protocol.log, self.configuration)
      protocol.connection.protocol = protocol
      return protocol

class DendriteClientFactory(protocol.ClientFactory):
   connection = high_level.ClientSideConnection
   protocol = low_level.DendriteClientProtocol
   
   def __init__(self, configuration):
      self.configuration = configuration
   
   def buildProtocol(self, *address):
      protocol = self.protocol(is_logging_all_packets=False)
      protocol.factory = self
      protocol.connection = self.connection(protocol.log, self.configuration)
      protocol.connection.protocol = protocol
      return protocol