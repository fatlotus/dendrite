# Primary dendrite protocol handler.

from twisted.internet import defer
import logging

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
   
   # Constructors
   def __init__(self, storage_backend, api_backend):
      self.storage_backend = storage_backend
      self.api_backend = api_backend
   
   # Global handlers
   def connected(self, sender):
      # Initialize the per-connection session.
      sender.session['identcback'] = defer.Deferred()
      sender.session['backend_info'] = None
      
      # Default behaviour to require a identity before
      # any sort of request. Thus, send a request and only
      # then trigger the Deferred from it.
      def got_identity(sender, userAgent, deviceID):
         sender.session['identcback'].callback((userAgent, deviceID))
      
      # Bother the client asynchronously.
      sender.identify(identity=got_identity)
      
   def handle_login(self, sender, username, password):   
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
      
      session = sender.session['backend_info']
      req = self.api_backend.Request(session, method, url, query_string, body)
      
      req.fetch (
         self.curry(sender, sender.data),
         self.curry(sender, sender.failure)
      )
   
   @secure
   def handle_listen(self, sender, url, query_string):
      
      session = sender.session['backend_info']
      req = self.api_backend.Request(session, method, url, query_string, body)
      
      req.listen (
         self.curry(sender, sender.notify),
         self.curry(sender, sender.failure)
      )
      
      sender.success(cancel=req.cancel)