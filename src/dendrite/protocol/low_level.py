from twisted.internet import protocol 
import struct

PACKET_HEADER = "!IBI"

class DendriteServerProtocol(protocol.Protocol):
	def packetReceived(self, message):
		print "packet %i (type = %i) {" % (self.message_id, self.kind)
		print "  reply %i" % self.reply
		print "  contents %s" % repr(message)
		print "}"
	
	def connectionMade(self):
		self.buffer = ""
		self.length = -1
		self.message_id = 0
		self.reply = None
		self.kind = None
	
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
					self.message_id += 2
				else:
					break

class DendriteClientProtocol(protocol.Protocol):
	def sendPacket(self, reply, kind, message):
		self.transport.write(struct.pack(PACKET_HEADER, reply, kind, len(message)))
		self.transport.write(message)
	
	def connectionMade(self):
		self.sendPacket(0, 0x1, "Hello, world!")