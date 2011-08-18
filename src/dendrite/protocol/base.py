# This class handles the processing and
# serialization of Dendrite protocol packets.
#
# For protocol information, see the Dendrite
# specification, which contains detailed 
# information about all the various packet
# fields and options.

from twisted.internet import protocol, ssl, address
import struct
from dendrite.protocol import types, coding
import urlparse
import logging

__all__ = [ "DendriteProtocol" ]

# Packet header format.
# 
# See the specification for details.
PACKET_HEADER = struct.Struct('!IBI')

# URL Connection Method

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
      self.reply_to = reply_to
      self.session = protocol.session
      
      if reply_to:
         # If I'm not a global handler, then set
         # it to be one.
         self.origin = self.protocol.global_handler
      else:
         # Otherwise just set it to self.
         self.origin = self
   
   # This class method installs a proxy method for the
   # specified protocol message type name.
   @classmethod
   def _install(klass, name):
      def inner(self, *fields, **responders):
         return self.protocol.send(name, self.reply_to, fields, responders)
      
      setattr(klass, name, inner)

# We need to patch the _sender class so that every possible
# message type has a proxy method defined.
for name in types.TYPE_IDS.keys():
   _sender._install(name)

class DendriteProtocol(protocol.Protocol):
   # Public constructor. Adapter can be null, in which case
   # it must be set later via proto.adapter = _.
   def __init__(self, is_initiator, adapter=None, identifier=""):
      self.adapter = adapter
      self.buffer = ""
      self.header = None
      self.is_initiator = is_initiator
      self.incoming_nonce = 0 if is_initiator else 1
      self.outgoing_nonce = 1 if is_initiator else 0
      self.reply_handlers = { }
      
      # This variable warrants further explanation: it is used to
      # track per-connection state, and so will never be used within
      # this class, since that is application-specific. It is
      # accessible through _sender#session, however, and that is 
      # the preferred way of accessing it.
      # 
      # Note that this value must never be reassigned: since the
      # dict type is mutable, all mutations must be to the same
      # instance, lest we risk inconsistent state across 
      # references.
      self.session = { }
      
      # The global handler is a proxy object that sends objects
      # with no "reply-to" field. In an RPC metaphor, it
      # encapsulates the "default callee" whenever there is
      # none to reply to.
      self.global_handler = _sender(self, None)
       
   
   ### Public API ###
   #
   
   # This helper method creates a twisted.internet.Factory
   # instance suitable for running this Protocol. This factory,
   # conveniently enough, also duck-types as an SSL context 
   # factory that can be used for calls like connectSSL and 
   # listenSSL.
   # 
   # Unlike the constructor above, the adapter parameter
   # is not optional.
   @classmethod
   def build_factory(klass, adapter, is_initiator):
      # Create an annonymous factory. Is it bad that we just made
      # a static metafactory?
      
      class _Factory(protocol.ClientFactory, ssl.DefaultOpenSSLContextFactory):
         def __init__(self):
            pass
         
         # This is the only method defined for the type *ContextFactory
         # 
         # (Duck-typing can be quite convenient in situations like this!)
         def getContext(self):
            if is_initiator:
               # Client authentication using SSL is optional.
               if hasattr(adapter, "provide_client_ssl_context"):
                  return adapter.provide_client_ssl_context()
               else:
                  # If the adapter doesn't provice client authentication,
                  # then assume that there is none.
                  return ssl.ClientContextFactory().getContext()
            else:
               # The adapter must provide a server SSL context
               # since servers are always authenticated.
               return adapter.provide_server_ssl_context()
         
         # Builds an instance of klass, as appropriate.
         def buildProtocol(self, address):
            return klass(is_initiator, adapter, identifier=address)
      
      return _Factory()
   
   # This helper connects to the Dendrite instance running on
   # the specified url with the specified adapter, and runs the
   # protocol as with a normal connection.
   # 
   # This method uses URL parsing internally, and, at the moment,
   # only supports TCP (with or without SSL), and UNIX domain
   # sockets. Any HTTP-specific URL features are ignored.
   #
   # For TCP connections, the default port for Dendrite is 1337.
   # 
   # Ex.
   # 
   # tcp://hostname:80 => CONNECT TCP hostname PORT 80
   # tcp://hostname => CONNECT TCP hostname PORT 1337
   # ssl://hostname:1337 => CONNECT TCP WITH SSL hostname PORT 1337
   # unix://tmp/connect.sock => CONNECTS TO ./tmp/connect.sock
   # unix:///tmp/connect.sock => CONNECTS TO /tmp/connect.sock
   #
   @classmethod
   def connect(klass, reactor, url, adapter, **dargs):
      fac = self.build_factory(adapter, is_initiator=True)
      
      result = urlparse.urlparse(url)
      
      if result.scheme == 'ssl':
         reactor.connectSSL(result.hostname, result.port or 1337, fac, fac, **dargs)
      elif result.scheme == 'tcp':
         reactor.connectTCP(result.hostname, result.port or 1337, fac, **dargs)
      elif result.scheme == 'unix':
         reactor.connectUNIX("%s%s" % (result.hostname, result.path), **dargs)
      else:
         raise ValueError("Unsupported URL scheme: %s" % repr(result.scheme))
   
   # This helper listens to the Dendrite instance running on
   # the specified url with the specified adapter, and runs the
   # protocol as with a normal connection.
   # 
   # This method uses URL parsing internally, and, at the moment,
   # only supports TCP (with or without SSL), and UNIX domain
   # sockets. Any HTTP-specific URL features are ignored.
   #
   # For TCP connections, the default port for Dendrite is 1337.
   # 
   # Ex.
   # 
   # tcp://hostname:80 => LISTEN PORT 80
   # tcp://hostname => LISTEN PORT 1337
   # ssl://hostname:1337 => LISTEN TCP WITH SSL PORT 1337
   # unix://tmp/connect.sock => CONNECTS TO ./tmp/connect.sock
   # unix:///tmp/connect.sock => CONNECTS TO /tmp/connect.sock
   #
   @classmethod
   def listen(klass, reactor, url, adapter, **dargs):
      fac = klass.build_factory(adapter, is_initiator=False)

      result = urlparse.urlparse(url)

      if result.scheme == 'ssl':
         return reactor.listenSSL(result.port or 1337, fac, fac, **dargs)
      elif result.scheme == 'tcp':
         return reactor.listenTCP(result.port or 1337, fac, **dargs)
      elif result.scheme == 'unix':
         return reactor.listenUNIX("%s%s" % (result.hostname, result.path), **dargs)
      else:
         raise ValueError("Unsupported URL scheme: %s" % repr(result.scheme))
   
   ### Helper methods ###
   # 
   
   # Handles any unspecified protocol errors.
   # 
   # Unlike raise, exc can be either a str or 
   # an Exception.
   def handle_protocol_error(self, exc=None):
      
      # Check to see if the adapter can deal with it.
      if hasattr(self.adapter, "handle_protocol_error"):
         
         # Allow the adapter time to send a "failure" response,
         # if it desires, but ensure that the protocol is always
         # closed.
         self.adapter.handle_protocol_error(exc)      
         self.transport.loseConnection()
      else:
         
         # If we're not handling the exception, still close it,
         # but also raise an exeption (which Twisted will log.)
         self.transport.loseConnection()
         raise Exception(exc)
   
   # Sends a message given the reply_to fields
   # and arguments. This method is not designed
   # to be user-facing, as the ugly-looking
   # method signature would imply.
   # 
   # Reply-to is a message ID or None.
   # Args is a list of (strongly-typed) arguments.
   # Responses is a mapping of message type names to
   #  lambdas.
   def send(self, message_name, reply_to, args, responses):
      # If this is a global message, then set the reply-to
      # to be the outgoing message ID.
      if reply_to is None:
         reply_to = self.outgoing_nonce
      
      # If there are any responses, then record them for later.
      #
      # We copy the dict of responses just for safety. It's often
      # easier if mutable types are protected, particularly in 
      # dynamic languages like Python.
      
      self.reply_handlers[self.outgoing_nonce] = responses.copy()
      
      # Get the numeric type ID from the mapping.
      try:
         message_type = types.TYPE_IDS[message_name]
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
      
      # Extra validation step for prettier validations.
      if len(argument_types) != len(args):
         raise TypeError("API call %s takes %i argument(s) (%i given)" %
            (repr(message_name), len(argument_types), len(args))
         )
      
      # Encode the message arguments given the types.
      # 
      # Any errors in message packing are the fault of the 
      # user. Blame him, and do not mask backtraces.
      message_body = coding.encode(argument_types, args)
      
      #LOGGING
      
      # Construct the header, and write it to the stream.
      header = (reply_to, message_type, len(message_body))
      self.transport.write(PACKET_HEADER.pack(*header))
      
      # Write the message body out to the stream as well.
      self.transport.write(message_body)
      
      # Increment the nonce
      self.outgoing_nonce += 2
   
   ### Twisted callbacks ###
   # 
   # (with their strange camelCased
   # callback names... ugh.)
   
   # Called when the connection has been made, as would seem 
   # relatively self-explanatory. This method is useful for 
   # sending the initial TLS request and beginning
   # protocol interchange.
   def connectionMade(self):
      if hasattr(self.adapter, 'connected'):
         self.adapter.connected(self.global_handler)
   
   # Called whenever the connection is lost, for whatever
   # reason. This should be used for general cleanup information
   # and logging, depending on what "reason" is.
   def connectionLost(self, reason):
      if hasattr(self.adapter, 'disconnected'):
         self.adapter.disconnected(self.global_handler, reason)
   
   
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
               # If the buffer is too small, then wait for more data.
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
               self.buffer = self.buffer[self.header[2]:]
               
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
               
               #LOGGING
               
               # Retrieve the statically-allocated field types from the list.
               try:
                  argument_types = types.FIELD_TYPES[type_name]
               except KeyError:
                  handle_protocol_error (
                    'No argument types for type name %s' % type_name
                   )
               
               try:
                  args = coding.decode(message_body, argument_types)
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
               if in_reply_to == message_id:
                  
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
                  if (in_reply_to % 2) != (self.outgoing_nonce % 2):
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
                  if in_reply_to >= self.outgoing_nonce:
                     self.handle_protocol_error (
                        'Message validation error: received message that could '
                        'not have been sent'
                     )
                     return
                  
                  # For non-global messages (replies), look up the handler and
                  # retrieve the message.
                  try:
                     handlers = self.reply_handlers[in_reply_to]
                     handler = handlers[type_name]
                  except KeyError:
                     self.handle_protocol_error (
                        'No reply handler in %i '
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
                     self.reply_handlers[in_reply_to] = handlers

                  sender.expect_more = _closure_expect_more_messages
                  
                  # Forget by default.
                  # 
                  # Only you can prevent reference cycles.
                  del self.reply_handlers[in_reply_to]
               
               # Trigger the handler given the origin message.
               handler(sender, *args)
               
               # Increment the incoming message nonce.
               self.incoming_nonce += 2
               
               # Clear the header fields, so that we can load another one.
               self.header = None
               
            # If nothing else, then break out of the loop. We can't parse
            # anything more, so return to the event loop.
            else:
               break