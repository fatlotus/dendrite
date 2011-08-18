# Primary dendrite protocol handler.

from twisted.internet import defer, ssl
from OpenSSL import rand
import logging
from dendrite.controllers import session_helper

class Controller(object):
   # Helper annotations and functions
   def secure(func):
      def inner(self, sender, *vargs, **dargs):
         if sender.session['backend_info'] is not None:
            return func(self, sender, *vargs, **dargs)
         else:
            sender.failure (
              "AuthenticationRequired",
              "That request requires authentication."
            )
      return inner
   
   def curry(self, sender, func):
      def inner(*vargs, **dargs):
         if sender.session['backend_info'] is not None:
            return func(*vargs, **dargs)
         else:
            pass
      return inner
   
   def __init__(self, api_backend, storage_backend):
      """
      Instantiate this frontend instance given an API and
      generic storage backend. This method also initializes
      the SSL context factory, which caches the certificate
      and private key for the duration of the server 
      instance lifecycle.
      """
      self.storage_backend = storage_backend
      self.api_backend = api_backend
      self.context_factory = ssl.DefaultOpenSSLContextFactory (
         'config/keys/localhost.key',
         'config/keys/localhost.crt',
      )
      self.stored_session_private_key = rand.bytes(1024)
   
   def provide_server_ssl_context(self):
      """
      Initializes a server-side SSL context for a newly-formed
      connection. This method is called before #connected. In
      this implementation, the code fetches the keys from
      config/keys/server.key and config/keys/server.pem
      """
      
      return self.context_factory.getContext()
   
   def connected(self, sender):
      """
      This method is called by base.DendriteProtocol whenever a
      new connection is made to this server. This method should
      not be called by anything else, as the argument "sender"
      is of an inner class of protocol.base.
      
      On a protocol level, this method queries the other side
      with an "identify" and request and initializes the
      connection.
      """
      
      # Initialize the per-connection session.
      sender.session['identcback'] = defer.Deferred()
      sender.session['backend_info'] = None
      
      # Default behaviour to require a identity before
      # any sort of request. Thus, send a request and only
      # then trigger the Deferred from it.
      def got_identity(sender, user_agent, device_id):
         sender.session['user_agent'] = user_agent
         sender.session['device_id'] = device_id
         sender.session['identcback'].callback(True)
      
      # Bother the client asynchronously.
      sender.identify(identity=got_identity)
      
   def handle_login(self, sender, username, password):
      """
      Handle a login request.
      """
      
      def try_authentication(identity):
         def authentication_success(session):
            sender.session['backend_info'] = session
            sender.success()
      
         def authentication_failed(exc):
            sender.session['backend_info'] = None
            sender.failure('AuthenticationFailed', 'Invalid username or password.')
            return ""
         
         d = self.api_backend.authenticate(username, password)
         d.addCallback(authentication_success)
         d.addErrback(authentication_failed)
      
      sender.session['identcback'].addCallback(try_authentication)
   
   # These two methods are largely just curried wrappers around the 
   # methods in backend. This is intentional: this layer only handles
   # protocol details in order to keep the code clean and understandable.
   @secure
   def handle_fetch(self, sender, method, url, query_string, body):
      """
      A secured API handler that triggers a REST request on the API
      backend. See the protocol specification for details.
      """
      
      session = sender.session['backend_info']
      req = self.api_backend.Request(session, method, url, query_string, body)
      
      req.fetch (
         self.curry(sender, sender.data),
         self.curry(sender, sender.failure)
      )
   
   @secure
   def handle_listen(self, sender, url, query_string):
      """
      A secured API handler that begins notifying the client of
      updates to the specified REST request. The request type is
      always GET, and the request body is empty.
      
      See the specification for more details.
      """
      session = sender.session['backend_info']
      req = self.api_backend.Request(session, method, url, query_string, body)
      
      req.listen (
         self.curry(sender, sender.notify),
         self.curry(sender, sender.failure)
      )
      
      sender.success(cancel=req.cancel)
   
   @secure
   def handle_session(self, sender):
      """
      A secured API handler that gets the current session as a
      flat string that can be stored for a later time. The client
      can then, hopefully, log back in later with the RESTORE
      method call.
      """
      
      # Extract the login-relevant subsession.
      login_session = sender.session['backend_info']
      
      # Call the session helper to decrypt the data.
      data = session_helper.save(self.stored_session_private_key, login_session)
      
      # Return it to the client.
      sender.text(data)