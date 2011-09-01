from twisted.internet import protocol, defer
import struct

FAILURE_CODE = "-----TRIGGER-FAILURE-----"

class Service(protocol.Protocol, protocol.ServerFactory):
   def __init__(self):
      self.stages = [defer.Deferred(), defer.Deferred(), defer.Deferred()]
      self.apns = None
      self.triggered = [ False, False, False ]
   
   def connectionMade(self):
      self.buffer = ""
      self.stages[0].callback(True)
      self.triggered[0] = True
      
   def dataReceived(self, data):
      self.buffer += data
      
      if len(self.buffer) > 20 and not self.triggered[1]:
         self.stages[1].callback(True)
         self.triggered[1] = True
      
      if FAILURE_CODE in self.buffer and not self.triggered[2]:
         self.transport.write(struct.pack('!BBI', 8, 8, 42))
         self.transport.loseConnection()
         self.stages[2].callback(True)
         self.triggered[2] = True
   
   def buildProtocol(self, address):
      return self