# Primary dendrite protocol handler.

from twisted.internet import defer, ssl
from OpenSSL import rand
import logging
from dendrite.controllers import session_helper
from dendrite import Component

class Controller(Component):
   # Helper annotations and functions
   def secure(func):
      def inner(self, sender, *vargs, **dargs):
         if sender.session['auth'] is not None:
            return func(self, sender, *vargs, **dargs)
         else:
            sender.failure('LoginRequired', 'That API call requires authentication.')
            logging.error('Attempted to access %s(..) without authentication' %
              func.__name__)
            # sender.close()
      return inner
   
   def curry(self, sender, func):
      def inner(*vargs, **dargs):
         if sender.session['auth'] is not None:
            return func(*vargs, **dargs)
         else:
            pass
      return inner
   
   def __init__(self,
    certificate='config/keys/localhost.crt', 
    private_key='config/keys/localhost.key'):
      
      """
      Instanitate this frontend connecition controller.
      
      Each controller object handles many individual
      connections and login sessions, so we cannot trust
      instance variables with user-specific state.
      
      This method also initializes the SSL context factory,
      which caches the certificate and private key for the
      duration of the server instance lifecycle.
      """
      
      self.context_factory = ssl.DefaultOpenSSLContextFactory (
         private_key,
         certificate,
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
   
   def handle_protocol_error(self, sender, err):
      """
      Handles a protocol error. The base.py module will close
      the connection regardless of what happens in this method,
      so this method is more for reporting of the error than 
      cleanup.
      """
      
      error = 'Protocol error: %s\n%s' % (err.getErrorMessage(), err.getTraceback)
      
      logging.error(error)
      
      sender.failure("ProtocolError", "A protocol error has occured.")
   
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
      sender.session['auth'] = None
      
      # Default behaviour to require a identity before
      # any sort of request. Thus, send a request and only
      # then trigger the Deferred from it.
      def got_identity(sender, user_agent, device_id):
         logging.info('User-agent: %s' % repr(user_agent))
         logging.info('Device-id:  %s' % repr(device_id))
         sender.session['user_agent'] = user_agent
         sender.session['device_id'] = device_id
         sender.session['identcback'].callback(True)
      
      # Bother the client asynchronously.
      sender.identify(identity=got_identity)
      
      logging.info('Connected.')
   
   def disconnected(self, sender, reason):
      logging.info('Disconnected: %s' % reason)
   
   def handle_login(self, sender, username, password):
      """
      Handle a login request.
      """
      
      def try_authentication(identity):
         def authentication_success(authctx):
            logging.info('Login success for %s' % repr(username))
            
            sender.session['auth'] = authctx
            sender.session['auth']['device_id'] = sender.session['device_id']
            sender.session['auth']['user_agent'] = sender.session['user_agent']
            sender.success()
      
         def authentication_failed(exc):
            logging.info('Login failed for %s' % repr(username))
            
            sender.session['auth'] = None
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
      
      session = sender.session['auth']
      resource = self.api_backend.resource(session, method, url, query_string, body)
      
      resource.fetch (
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
      
      session = sender.session['auth']
      resource = self.api_backend.resource(session, 'GET', url, query_string, '')
      
      resource.listen (
         self.curry(sender, sender.notify),
         self.curry(sender, sender.failure)
      )
      
      sender.success(cancel=lambda sender: resource.cancel())
   
   @secure
   def handle_session(self, sender):
      """
      A secured API handler that gets the current session as a
      flat string that can be stored for a later time. The client
      can then, hopefully, log back in later with the RESTORE
      method call.
      """
      
      # Extract the login-relevant subsession.
      login_session = sender.session['auth']
      
      # Call the session helper to decrypt the data.
      data = session_helper.save(self.stored_session_private_key, login_session)
      
      # Return it to the client.
      sender.text(data)
   
   def handle_restore(self, value):
      """
      An unsecured API handler that restores only the authentication
      portion of a saved session handler. Right now, restoration is
      hard-disabled pending a proper security review.
      """
      
      logging.warn("Restore method called but it is disabled.")
      
      sender.failure()