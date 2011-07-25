from twisted.internet import protocol
from dendrite.protocol import coding
from dendrite.protocol import types
import struct

PACKET_HEADER = "!IBI"

class DendriteServerProtocol(protocol.Protocol):
	def __init__(self):
		self.buffer = ""
		self.length = -1
		self.received_message_id = 1
		self.sent_message_id = 0
		self.reply = None
		self.kind = None
	
	def packetReceived(self, message):
		print "PACKET: %s" % types.FIELD_TYPES.get(self.kind, "(unknown kind)")
	
	def sendPacket(self, kind, reply=None, fields=[ ]):
		if reply == None:
			reply = self.sent_message_id
		
		field_types = zip(types.FIELD_TYPES[kind], fields)
		message = coding.encode(field_types)
		
		header = struct.pack(PACKET_HEADER,
			reply,
			types.TYPE_IDS[kind],
			len(message)
		)
		self.transport.write(header)
		self.transport.write(message)
		self.sent_message_id += 2
	
	def connectionMade(self):
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
					self.length = -1
					self.received_message_id += 2
				else:
					break

class DendriteClientProtocol(protocol.Protocol):
	def sendPacket(self, reply, kind, message):
		self.transport.write(struct.pack(PACKET_HEADER, reply, kind, len(message)))
		self.transport.write(message)
	
	def dataReceived(self, data):
		print repr(data)
	
	def connectionMade(self):
		pass