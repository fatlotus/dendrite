from twisted.internet import protocol, ssl, defer
import json
import struct

NOTIFICATION_DELAY = 3600 * 24 # 24-hours

class APNProtocol(protocol.Protocol):
   def __init__(self):
      """
      Initialize this protocol instance.
      """
      
      # Initialize a buffer for receiving (fatal) errors from the APNs.
      self.buffer = ""
   
   def connectionMade(self):
      """
      Handles a connection made to the server. The APNs protocol does not
      specify any protocol initiation options here, so we can get away with
      no initialization.
      """
      
      # However, we do want to trigger the connection callback, if 
      # necessary.
      # 
      # Klugey? Yes, I know.
      if hasattr(self.factory, "deferred"):
         self.factory.deferred.callback(self)
   
   def dataReceived(self, data):
      """
      Processes a message from the server. This is largely just to handle
      error messages returned from notification messages.
      
      Hopefully, any errors are already ironed out before production, so
      this 
      
      """
      
      # Buffer the incoming message.
      self.buffer += data
      
      # If we've got enough for an error (according to the spec),
      # then load it and parse it.
      #
      if len(self.buffer) >= 6:
         
         # Process it as standard APNs response code.
         (command, status, identifier) = struct.unpack('!BBI', self.buffer[:6])
         
         # This could be considered an assert statement, but those 
         # are often disabled in production. This could indicate
         # a change in the Apple push notification API.
         # 
         if command != 8:
            raise AssertionError("Invalid response code %i." % command)
         
         # Prepare a mapping of error codes to names.
         errors = {
            0 : "No errors encountered",
            1 : "Processing error",
            2 : "Missing device token",
            3 : "Missing token",
            4 : "Missing payload",
            5 : "Invalid token size",
            6 : "Invalid topic size",
            7 : "Invalid payload size",
            8 : "Invalid token",
            255 : "None (unknown)"
         }
         
         # Determine what the error message actually was.
         message = errors.get(status, 'Error type %i' % status)
         
         # Advance the buffer before exiting.
         self.buffer = self.buffer[6:]
         
         # Throw the exception. This is intentionally disruptive:
         # we want to ensure that the overall service crashes when
         # the APNs has failed, since most of the errors are
         # fatal or endemic of developer error. In any case, a
         # failure here is unrecoverable.
         raise AssertionError("APN internal error: %s" % message)
   
   def notify(self, deviceID, alert=None, badge=None, sound=None):
      """
      Sends a notification to the specified deviceID with the given
      alert, badge, and sound. If alert or sound is None, then no
      alert or sound is played. If badge is None, then any badge
      currently displayed is hidden.
      
      For more information regarding the APNS protocol, see:
      
      http://developer.apple.com/library/ios/#documentation/
        NetworkingInternet/Conceptual/RemoteNotificationsPG/
        ApplePushService/ApplePushService.html#//apple_ref/doc/
        uid/TP40008194-CH100-SW10
      
      
      """
      
      # Construct the JSON object to send over the wire. There
      # can be other keys here, but we're only using the APNs
      # for background notification.
      data = { }
      
      if alert:
         data['alert'] = alert

      if badge:
         data['badge'] = badge

      if sound:
         data['sound'] = sound
      
      # Serialize the JSON to a string.
      payload = json.dumps(data)
      
      # Prepare the notification expiration time(as an integral
      # number of seconds, according to the Apple specification)
      #
      expiration = int(time.time() + NOTIFICATION_DELAY)
      
      # Assume that the deviceID has been sent as hexadecimal
      # over the wire for string safety. Since fields in Dendrite
      # are UTF-8, there's really no guarantee of binary safety.
      binaryDeviceID = deviceID.decode('hex')
      
      # Package the struct as a network-byte order protocol.
      #
      # Fields:
      # Sz. Name        Description
      # 1   Type        Always 1 (see the Apple docs).
      # 4   Identifier  A user-specified identifier for error
      #                 tracking and handling.
      # 4   Expiration  Used to handle retries (see docs)
      # 2   Length
      #     DeviceID    The DeviceID (in binary).
      # 2   Length
      #     Payload     The serialized JSON to send.
      
      packet = (
         struct.pack('!BIIH', 1, 0, expiration, len(binaryDeviceID)) +
         binaryDeviceID +
         struct.pack('!H', len(payload)) +
         payload
      )
      
      # Write the packet out to the stream.
      self.transport.write(packet)
      
   
   @classmethod
   def build_factory(klass, certificate, private_key):
      """
      Standard helper method to create a static-meta-factory to
      deal with the twisted ugliness for us. This allows for dependency 
      injection later, but without the nasty protocol handling bits now.
      
      The returned factory is duck-typed with a ClientContextFactory,
      so it can be used as both the protocol and the ssl context in
      a connectSSL call.
      
      If you'd like, you can wait for the #deferred property on the returned
      Factory subclass to get the new protocol instance.
      """
      
      class _Factory(protocol.ClientFactory, ssl.ClientContextFactory):
         def getContext(self):
            
            # By default, ClientContext factories do not include
            # client authentication. Instead, override the default
            # behavior and add in the given certificate information.
            # 
            ctx = ssl.ClientContextFactory.getContext(self)
            ctx.use_certificate_file(certificate)
            ctx.use_privatekey_file(private_key)
            
            return ctx
         
         # Set the protocol to be the correct APNs parser.
         protocol = klass
      
      # Create a deferred and attach it to the factory subclass. This
      # is simultaneously a class method and an instance property _at
      # the same time_.
      _Factory.deferred = defer.Deferred()
      
      return _Factory()
