from OpenSSL import SSL
from twisted.internet import protocol, ssl
from dendrite.protocol import coding
from dendrite.protocol import types
import struct

PACKET_HEADER = "!IBI"

class DendriteProtocol(protocol.Protocol):
   def __init__(self):
      self.buffer = ""
      self.length = -1
      self.received_message_id = 1 if self.is_server_side else 0
      self.sent_message_id     = 0 if self.is_server_side else 1
      self.reply = None
      self.kind = None
      self.replies = dict( )
   
   def packetReceived(self, message):
      type_name = types.INVERTED_TYPE_IDS[self.kind]
      message_id = self.received_message_id
      fields = coding.decode(message, types.FIELD_TYPES[type_name])
      reply_id = self.reply
      
      def reply(kind, *args):
         self.sendPacket(kind, message_id, *args)
      
      if reply_id != self.received_message_id:
         def cancel():
            del self.replies[reply_id]
         
         try:
            method = self.replies[reply_id]
            method(type_name, reply, cancel, *fields)
         except KeyError:
            raise ValueError("Received a reply to a message I'm not"
             "waiting for: %i" % reply_id)
      else:
         method = getattr(self.connection, "received_%s" % type_name)
         method(reply, *fields)
   
   def sendPacket(self, kind, reply=None, *fields):
      if reply == None:
         reply = self.sent_message_id
      
      if len(fields) >= 1 and callable(fields[0]):
         self.replies[self.sent_message_id] = fields[0]
         
         fields = fields[1:]
      
      field_types = zip(types.FIELD_TYPES[kind], fields)
      message = coding.encode(field_types)
      
      header = struct.pack(PACKET_HEADER, reply, types.TYPE_IDS[kind], len(message))
      
      self.transport.write(header)
      self.transport.write(message)
      self.sent_message_id += 2
   
   def connectionMade(self):
      def send(kind, *fields):
         self.sendPacket(kind, None, *fields)
      
      def startTLS(is_server=False):
         if is_server:
            ctx = ssl.DefaultOpenSSLContextFactory(
               privateKeyFileName='config/keys/server.key',
               certificateFileName='config/keys/server.crt'
            )
            self.transport.startTLS(ctx, self.factory)
         else:
            ctx = ssl.ClientContextFactory()
            self.transport.startTLS(ctx, self.factory)
      
      self.connection.startTLS = startTLS
      self.connection.send = send
      self.connection.initialize_connection()
   
   def dataReceived(self, data):
      self.buffer += data

      while True:
         if self.length < 0:
            l = struct.calcsize(PACKET_HEADER)

            if len(self.buffer) >= l:
               d = struct.unpack(PACKET_HEADER, self.buffer[:l])
               (self.reply, self.kind, self.length) = d
               self.buffer = self.buffer[l:]
            else:
               break

         if self.length >= 0:
            if len(self.buffer) >= self.length:
               self.packetReceived(self.buffer[:self.length])
               self.buffer = self.buffer[self.length:]
               self.length = -1
               self.received_message_id += 2
            else:
               break


class DendriteServerProtocol(DendriteProtocol):
   is_server_side = True

class DendriteClientProtocol(DendriteProtocol):
   is_server_side = False