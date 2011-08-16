class Controller(object):
   def __init__(self, test):
      self.test = test
      self.events = [ ]
   
   # Helpers
   def event(self, name):
      self.events.append(name)
   
   # Global callbacks
   def handle_protocol_error(self, error):
      self.test.tearDown()
      self.test.fail("Protocol error: %s" % error)
   
   def handle_failure(self, sender, failure, message):
      self.test.tearDown()
      self.test.fail("Foreign error: %s" % message)
   
   def connected(self, sender):
      sender.login ('fred', 'fredspassword',
         success=self.authenticated,
         failure=self.authfailure,
      )
   
   # Fetch callbacks
   def fetched_data(self, sender, data):
      self.event('data')
      
      self.test.tearDown()
   
   # Authentication callbacks
   def authenticated(self, sender):
      if 'identify' not in self.events:
         self.test.fail("Allowed entry without device identification.")
      
      if 'auth-bad' not in self.events:
         self.test.fail("Allowed phoney credentials into server.")
      
      self.event('auth-ok')
      
      sender.origin.fetch('GET', 'dendrite/aboutme', '', '', data=self.fetched_data,
         failure=self.handle_failure)
   
   def authfailure(self, sender, failure, message):
      self.event('auth-bad')
      sender.origin.login ('fatlotus', 'test',
         success=self.authenticated,
         failure=self.authfailure,
      )
   
   # Global callbacks
   def handle_identify(self, sender):
      self.event("identify")
      sender.identity("Python Integration Test", "")