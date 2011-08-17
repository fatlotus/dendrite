from twisted.internet import reactor
from nose.tools import *

class Controller(object):
   def __init__(self):
      self.events = [ ]
   
   # Helpers
   def event(self, name):
      self.events.append(name)
   
   def shutdown(self, error=None):
      try:
         reactor.stop()
      except:
         pass
      
      if error:
         fail(error)
   
   # Global callbacks
   def handle_protocol_error(self, error):
      self.shutdown("Protocol error: %s" % error)
   
   def handle_failure(self, sender, failure, message):
      self.shutdown("Foreign error: %s" % message)
   
   def connected(self, sender):
      def success(*vargs):
         self.shutdown (
            'Allowed to perform action without authentication.')
      
      def failure1(sender2, failure, message):
         def failure2(sender3, failure, message):
            sender.login ('fred', 'fredspassword',
               success=self.authenticated,
               failure=self.authfailure,
            )
            
         sender.listen('', '',
            failure=failure2,
            success=success,
            listen=success
         )
      
      sender.fetch('GET', '', '', '',
         failure=failure1,
         data=success
      )
   
   # Fetch callbacks
   def fetched_data(self, sender, data):
      self.event('data')
      
      self.shutdown()
   
   # Authentication callbacks
   def authenticated(self, sender):
      if 'identify' not in self.events:
         self.shutdown("Allowed entry without device identification.")
      
      if 'auth-bad' not in self.events:
         self.shutdown("Allowed phoney credentials into server.")
      
      self.event('auth-ok')
      
      sender.origin.fetch('GET', 'dendrite/aboutme', '', '',
         data=self.fetched_data,
         failure=self.handle_failure
      )
   
   def authfailure(self, sender, failure, message):
      if 'auth-bad' in self.events:
         self.shutdown("Blocked a valid (fake) user from the server.'")
      
      self.event('auth-bad')
      sender.origin.login ('test', 'test',
         success=self.authenticated,
         failure=self.authfailure,
      )
   
   # Global callbacks
   def handle_identify(self, sender):
      self.event("identify")
      sender.identity("Python Integration Test", "")