import unittest
from dendrite.protocol import low_level
from dendrite.protocol import types
from stub_helper import stub
import struct

class TestLowLevel(unittest.TestCase):
   def setUp(self):
      self.connection = object()
      
      self.protocol = low_level.DendriteServerProtocol()
      self.protocol.connection = self.connection
      self.next_packet_id = 1
   
   def ensure_nonse_parity(self):
      self.assertEqual(self.protocol.sent_message_id % 2, 0, "the server does not send even message IDs")
      self.assertEqual(self.protocol.received_message_id % 2, 1, "the server does not receive odd message IDs")
   
   def generate_packet(self):
      text = "abcdefghi"
      packet = struct.pack("!IBI", self.next_packet_id, types.TYPE_IDS["echo"], len(text)) + text
      
      self.next_packet_id += 2
      
      return (text, packet)
   
   def test_packet_parsed(self):
      proto = self.protocol
      
      self.ensure_nonse_parity()
      
      stub(proto, "packetReceived", replace=True)
      
      (text, packet) = self.generate_packet()
      
      for character in packet:
         self.assertEqual(proto.packetReceived.was_called(), False,
            "incomplete packet generates complete call.")
         proto.dataReceived(character)
      
      self.assertEqual(proto.packetReceived.was_called(), True,
         "complete packet does not call packetReceived")
      self.assertEqual(tuple(proto.packetReceived.vargs), (text,),
         "packet sent modifies packet contents")
      
      self.ensure_nonse_parity()
   
   def test_multiple_packets_parsed(self):
      proto = self.protocol
      
      for i in xrange(10):
         chunk_size = 7 * (i + 1)
         
         self.ensure_nonse_parity()
         
         stub(proto, "packetReceived", replace=True)
      
         (texts, packets) = zip(*([self.generate_packet()] * 42))
      
         stream = ''.join(packets)
         
         while len(stream) > 0:
            proto.dataReceived(stream[:chunk_size])
            
            stream = stream[chunk_size:]
         
         self.assertEqual(proto.packetReceived.times_called, 42,
            "mismatch in number of sent and received packets (SENT: 42, GOT: %i)"
            % proto.packetReceived.times_called)
         
         proto.packetReceived.reset()