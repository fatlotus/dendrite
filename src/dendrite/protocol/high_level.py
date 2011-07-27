from twisted.internet import reactor # FIXME
from dendrite import backends
import sys

class ServerSideConnection():
   def initialize_connection(self):
      self.startTLS(is_server=True)
      self.heartbeat()
      self._backend = backends.preferred()
      self._authenticated = False
   
   def heartbeat(self):
      def handle_response(name, reply, cancel):
         cancel()
      self.send("echo", handle_response)
      
      reactor.callLater(1, self.heartbeat)
   
   def received_login(self, reply_to_login, username, password):
      def get_user_info_succeeded(name, reply_to_identity,
       cancel, userAgent, deviceID):
         if name == 'identity':
            def login_succeeded(ignored):
               reply_to_login("success")
               self._authenticated = True
      
            def login_failed(err):
               reply_to_login("failure", err.getErrorMessage())
               self._authenticated = False
         
            d = self._backend.authenticate(username, password, info=userAgent)
            d.addCallback(login_succeeded)
            d.addErrback(login_failed)
            cancel()
      
      self.send("identify", get_user_info_succeeded)
   
   def received_fetch(self, reply, method, url):
      if self._authenticated:
         def fetch_response(data):
            reply("data", data)
         
         def failed(err):
            reply("failure", err.getErrorMessage())
         
         d = self._backend.fetch(method, url, '', '')
         d.addCallback(fetch_response)
         d.addErrback(failed)
      else:
         reply("failure", "The fetch command requires authentication.")
   

class ClientSideConnection():
   def initialize_connection(self):
      self.startTLS(is_server=False)
      
      def handle_response(name, reply, cancel, data):
         if name == "data":
            print "data: %s" % data
         elif name == 'failure':
            print "** protocol error: %s **" % data
         cancel()
      
      def handle_authenticate(name, reply, cancel, *error):
         if name == 'failure':
            print "** login failure: %s **" % error[0]
         else:
            self.send("fetch", handle_response, "GET", "/hello-world")
      
      self.send("login", handle_authenticate, "fred", "fredspassword")
   
   def get_user_agent(self):
      return ("Test/Python %s.%s.%s" % (sys.version_info.major,
         sys.version_info.minor, sys.version_info.micro), "(undefined)")
   
   def received_identify(self, reply):
      reply("identity", *self.get_user_agent())
   
   def received_echo(self, reply):
      reply("echo")