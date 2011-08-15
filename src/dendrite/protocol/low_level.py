from OpenSSL import SSL
from twisted.internet import protocol, ssl, defer
from dendrite.protocol import coding
from dendrite.protocol import types
import struct
import logging

PACKET_HEADER = "!IBI"

class PrefixFilter(object):
   def __init__(self, prefix):
      self.prefix = prefix
   
   def filter(self, record):
      record.msg = "%s: %s" % (self.prefix, record.msg)
      
      return record

class DendriteProtocol(protocol.Protocol):
   protocol_logger = logging.getLogger('protocol')
   nonce = 0
   
   def __init__(self, is_logging_all_packets=False):
      self.buffer = ""
      self.length = -1
      self.received_message_id = 1 if self.is_server_side else 0
      self.sent_message_id     = 0 if self.is_server_side else 1
      self.reply = None
      self.kind = None
      self.replies = dict( )
      self.is_logging = is_logging_all_packets
      
      DendriteProtocol.nonce += 1
      self.log = self.protocol_logger.getChild(str(DendriteProtocol.nonce))
      self.peer = "<unknown>:0"
   
   def handleException(self, exc):
      self.log.exception(exc)
      self.sendPacket("failure", "Error", "An error occurred.")
      self.tranport.close()
   
   def packetReceived(self, message):
      try:
         type_name = types.INVERTED_TYPE_IDS[self.kind]
         message_id = self.received_message_id
         fields = coding.decode(message, types.FIELD_TYPES[type_name])
         reply_id = self.reply
      
         def reply(kind, *vargs, **dargs):
            self.sendPacket(kind, reply=message_id, *vargs, **dargs)
      
         if reply_id != self.received_message_id:
            try:
               method = self.replies[reply_id]
               del self.replies[reply_id]
            
               def keep_waiting():
                  self.replies[reply_id] = method
            
               method(type_name, reply, keep_waiting, *fields)
            except KeyError:
               raise ValueError("%s received a reply to a message not "
                "waited for: %i" % ("Server" if self.is_server_side else "Client",
                 reply_id))
         else:
            method = getattr(self.connection, "received_%s" % type_name)
            method(reply, *fields)
      except Exception, e:
         self.handleException(e)
   
   def sendPacket(self, kind, *fields, **dargs):
      reply = None
      
      if "reply" in dargs:
         reply = dargs.get("reply", None)
         del dargs["reply"]
      
      if reply == None:
         reply = self.sent_message_id
      
      response = None
      
      if "response" in dargs:
         response = dargs.get("response")
      elif len(dargs) > 0:
         def response(name, reply, cancel, *fields):
            if name in dargs:
               dargs[name](reply, cancel, *fields)
            elif name == "failure":
               raise ValueError("unexpected failure: %s" % fields[0])
            else:
               raise ValueError("unexpected response: %s" % name)
      
      if response:
         self.replies[self.sent_message_id] = response
      
      message = coding.encode(types.FIELD_TYPES[kind], fields)
      
      header = struct.pack(PACKET_HEADER, reply, types.TYPE_IDS[kind], len(message))
      
      if self.is_logging:
         print "C<-S %s" % repr (dict (
            id = self.sent_message_id,
            reply = reply,
            kind = kind,
            body = message
         ))
      
      self.transport.write(header)
      self.transport.write(message)
      self.sent_message_id += 2
   
   def connectionMade(self):
      peer = "%s:%s" % (
         self.transport.getPeer().host,
         self.transport.getPeer().port
      )
      self.log.addFilter(PrefixFilter(peer))
      self.log.info("Connection made.")
      
      def send(*vargs, **dargs):
         self.sendPacket(reply=None, *vargs, **dargs)
      
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
   
   def connectionLost(self, reason=None):
      self.log.info("Connection lost: %s" % reason.getErrorMessage())
      
      self.connection.terminate_connection()
   
   def dataReceived(self, data):
      try:
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
                  if self.is_logging:
                     print "C->S %s" % repr (dict (
                        id = self.received_message_id,
                        reply = self.reply,
                        kind = types.INVERTED_TYPE_IDS[self.kind],
                        body = self.buffer[:self.length]
                     ))
                  self.packetReceived(self.buffer[:self.length])
                  self.buffer = self.buffer[self.length:]
                  self.length = -1
                  self.received_message_id += 2
               else:
                  break
      except Exception, e:
         self.handleException(e)


class DendriteServerProtocol(DendriteProtocol):
   is_server_side = True

class DendriteClientProtocol(DendriteProtocol):
   is_server_side = False