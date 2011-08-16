# This class handles the processing and
# serialization of Dendrite protocol packets.
#
# For protocol information, see the Dendrite
# specification, which contains detailed 
# information about all the various packet
# fields and options.

from twisted.internet import protocol
import struct
from dendrite.protocol import types, coding

__all__ = [ "DendriteProtocol" ]

# Packet header format.
# 
# See the specification for details.
PACKET_HEADER = struct.Struct('!IBI')

# Hidden wrapper class.
# 
# This class acts as a precompiled proxy for 
# treating RPC cleverly.
# 
# def controller_method(self, sender, *args):
#   sender.data({'success' : True})
# 
# 
class _sender(object):
   def __init__(self, protocol, reply_to):
      self.protocol = protocol

for name in types.TYPE_IDS.keys():
   def inner(*args):
      print "INNER: %s" % repr(args)
   
   setattr(_sender, name, inner)
   
   del inner

class DendriteProtocol(protocol.Protocol):
   def __init__(self, adapter=None, is_initiator=False):
      self.adapter = adapter
      self.buffer = ""
      self.header = None
      self.incoming_nonce = 0 if is_initiator else 1
      self.outgoing_nonce = 1 if is_initiator else 0
      self.reply_handlers = { }
   
   ### Helper methods ###
   # 
   
   # Handles any unspecified protocol errors.
   # 
   # Unlike raise, exc can be either a str or 
   # an Exception.
   def handle_protocol_error(self, exc=None):
      print repr(exc)
      # self.transport.loseConnection()
   
   # Sends a message given the reply_to fields
   # and arguments. This method is not designed
   # to be user-facing, as the ugly-looking
   # method signature would imply.
   # 
   # Reply-to is a message ID or None.
   # Args is a list of (strongly-typed) arguments.
   # Responses is a mapping of message type names to
   #  lambdas.
   def send(message_name, reply_to, args, responses):
      # If this is a global message, then set the reply-to
      # to be the outgoing message ID.
      if reply_to is None:
         reply_to = self.outgoing_message_nonce
      
      # If there are any responses, then record them for later.
      #
      # We copy the dict of responses just for safety. It's often
      # easier if mutable types are protected, particularly in 
      # dynamic languages like Python.
      self.reply_handlers[self.outgoing_message_nonce] = responses.copy()
      
      # Get the numeric type ID from the mapping.
      try:
         message_type = types.TYPE_IDs[message_name]
      except KeyError:
         raise ValueError("Unknown message type: %s" % message_name)
      
      # Fetch the argument types from the fields types mapping.
      # 
      # Generally, this error is not the fault of the caller,
      # but I figured it'd be helpful to note the callsites for 
      # ease-of-development.
      try:
         argument_types = types.FIELD_TYPES[message_name]
      except KeyError:
         raise ValueError("Message type %s has no argument types "
          "defined." % message_name)
      
      # Encode the message arguments given the types.
      # 
      # Any errors in message packing are the fault of the 
      # user. Blame him, and do not mask backtraces.
      message_body = coding.encode(message_arg_types, args)
      
      # Construct the header, and write it to the stream.
      header = (reply_to, message_type, len(message_body))
      self.transport.write(PACKET_HEADER.pack())
      
      # Write the message body out to the stream as well.
      self.transport.write(message_body)
      
      # Increment the nonce
      self.outgoing_nonce += 2
   
   ### Twisted callbacks ###
   # 
   # (with their strange camelCased
   # callback names... ugh.)
   
   # Called whenever there is new data to be processed on the TCP
   # stream, or whatever we're testing this against.
   def dataReceived(self, data):   
      self.buffer += data   
      
      # This is a loop to process multiple packets
      # in a single TCP packet. After that, the 
      # protocol is a simple two-step state
      # machine.
      #
      while True:
         
         # Handle the header fields first.
         if self.header is None:
            if len(self.buffer) >= PACKET_HEADER.size:
               
               # Unpack the message header, if possible.
               self.header = PACKET_HEADER.unpack_from(self.buffer)
               
               # Slide the buffer forward via slices.
               self.buffer = self.buffer[PACKET_HEADER.size:]
            else:
               # If the buffer is to small, then wait for more data.
               break
         
         # After ensuring that we have a header, process
         # the content of the message.
         if self.header is not None:
            if len(self.buffer) >= self.header[2]:
               
               # If possible, extract the message body given the 
               # header information.
               message_body = self.buffer[:self.header[2]]
               message_id = self.incoming_nonce
               in_reply_to = self.header[0]
               
               # Advance the receiving buffer (inefficiently)
               self.buffer = self.buffer[:self.header[2]]
               
               # We're using the standard Pythonic style of try: action
               # except: failure. This is somewhat slower (though the
               # Python VM gets better jump handling every release),
               # but it means that any uncaught failure cases are logged
               # as such.
               try:
                  type_name = types.INVERTED_TYPE_IDS.get(self.header[1])
               except KeyError:
                  # Every individual failure case _must_ be suffixed with a 
                  # "return" call, since handle_protocol_error does not raise
                  # an exception.
                  self.handle_protocol_error('Unknown type ID %i' % self.header[1])
                  return
               
               # Retrieve the statically-allocated field types from the list.
               try:
                  argument_types = types.FIELD_TYPES[type_name]
               except KeyError:
                  handle_protocol_error (
                    'No argument types for type name %s' % type_name
                   )
               
               try:
                  args = coding.decode(argument_types, message_body)
               except ValueError, e:
                  # The coding module should mask all other errors 
                  # and route them to ValueErrors.
                  self.handle_protocol_error(e)
                  return
               
               # Create and save a _sender proxy object for this message.
               sender = _sender(self, message_id)
               
               # A message that is its own reply is a global message.
               #
               # It's a bit obtuse, but it has no edge cases and means that
               # messages are self-describing.
               if message_id == self.incoming_nonce:
                  
                  # For global messages, just look up a handle_* method and 
                  # remember it.
                  try:
                     handler = getattr(self.adapter, "handle_%s" % type_name)
                  except AttributeError:
                     self.handle_protocol_error (
                       'No global handler for %s messages' % type_name)
                     return
                  
               else:
                  # Ensure that the reply_to is actually to a message I've sent.
                  #
                  # These sanity checks simply provide for a modicum of early
                  # error detection and response during development, and could
                  # be useful in the processing of an attack.
                  
                  # First, check that it is a message of a parity we could have
                  # sent.
                  if (in_reply_to % 2) != (self.outgoing_message_nonce % 2):
                     self.handle_protocol_error (
                        'Message parity error: received message that could not '
                        'have been sent.'
                     )
                     return
                  
                  # Now, check that it is a message that I could have sent.
                  # 
                  # This helps particularly with underflow, though that's
                  # rather unlikely to occur.
                  #
                  if in_reply_to >= self.outgoing_message_nonce:
                     self.handle_protocol_error (
                        'Message validation error: received message that could '
                        'not have been sent'
                     )
                     return
                  
                  # For non-global messages (replies), look up the handler and
                  # retrieve the message.
                  try:
                     handlers = self.replies[in_reply_to]
                     handler = handlers[type_name]
                  except KeyError:
                     self.handle_protocol_error (
                        'No reply handler for %i '
                        'for %s messages' % (in_reply_to, type_name)
                     )
                     return
                  
                  # Define a closure to handle the expectation of more data.
                  #
                  # By default, this protocol forgets that it was expecting
                  # messages unless explicitly told to re-register them. This
                  # helps prevent garbage-collection reference loops.
                  # 
                  # Curiously enough, this lambda actually helps retain the
                  # handlers by staying within the current stack context.
                  # 
                  # Sneaky, huh?
                  def _closure_expect_more_messages():
                     self.replies[in_reply_to] = handlers

                  sender.expect_more = _closure_expect_more_messages
                  
                  # Forget by default.
                  # 
                  # Only you can prevent reference cycles.
                  del self.replies[in_reply_to]
               
               # Trigger the handler given the origin message.
               handler(sender, *args)
               
               # Increment the incoming message nonce.
               self.incoming_nonce += 2
               
            # If nothing else, then break out of the loop. We can't parse
            # anything more, so return to the event loop.
            else:
               break