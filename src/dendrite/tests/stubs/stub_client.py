from twisted.internet import reactor, defer
from nose.tools import *

class Controller(object):
   def __init__(self):
      self.events = [ ]
      self.deferred = defer.Deferred()
   
   # Helpers
   def event(self, name):
      print "EVENTS: %s" % repr(self.events)
      self.events.append(name)
   
   def shutdown(self, error=None):
      if error:
         self.deferred.errback(Exception(error))
      else:
         self.deferred.callback('')
   
   # Global callbacks
   def handle_protocol_error(self, error):
      self.shutdown("Protocol error: %s" % error)
   
   def handle_failure(self, sender, failure, message):
      self.shutdown("Foreign error: %s" % message)
   
   def connected(self, sender):
      def success(*vargs):
         self.event("success")
         return self.shutdown (
            'Allowed to perform action without authentication.')
      
      def failure1(sender2, failure, message):
         def failure2(sender3, failure, message):
            self.event("failure2")
            
            sender.login ('fred', 'fredspassword',
               success=self.authenticated,
               failure=self.authfailure,
            )
            
         sender.listen('', '',
            failure=failure2,
            success=success,
            notify=success
         )
         
         self.event("failure1")
      
      sender.fetch('GET', '', '', '',
         failure=failure1,
         data=success
      )
      
      self.event("connected")
   
   # Fetch callbacks
   def fetched_data(self, sender, data):
      self.event('data')
      
      return self.shutdown()
   
   # Authentication callbacks
   def authenticated(self, sender):
      if 'identify' not in self.events:
         return self.shutdown("Allowed entry without device identification.")
      
      if 'auth-bad' not in self.events:
         return self.shutdown("Allowed phoney credentials into server.")
      
      self.event('auth-ok')
      
      sender.origin.fetch('GET', 'dendrite/aboutme', '', '',
         data=self.fetched_data,
         failure=self.handle_failure
      )
   
   def authfailure(self, sender, failure, message):
      if 'auth-bad' in self.events:
         return self.shutdown("Blocked a valid user from the server: %s" % message)
      
      self.event('auth-bad')
      sender.origin.login ('fatlotus', 'test',
         success=self.authenticated,
         failure=self.authfailure,
      )
   
   # Global callbacks
   def handle_identify(self, sender):
      self.event("identify")
      sender.identity("Python Integration Test", "")