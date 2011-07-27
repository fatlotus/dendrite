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
      def handle_response(reply, cancel):
         pass
      self.send("echo", echo=handle_response)
      
      reactor.callLater(1, self.heartbeat)
   
   def received_login(self, reply_to_login, username, password):
      def try_authenticate(userAgent):
         def login_succeeded(ignored):
            reply_to_login("success")
            self._authenticated = True
   
         def login_failed(err):
            reply_to_login("failure", err.getErrorMessage())
            self._authenticated = False
      
         d = self._backend.authenticate(username, password, info=userAgent)
         d.addCallback(login_succeeded)
         d.addErrback(login_failed)
      
      def identify_succeeded(reply, cancel, userAgent, deviceID):
         try_authenticate(userAgent)
      
      def identify_failed(reply, cancel, err):
         try_authenticate("(unknown)")
      
      self.send("identify", identity=identify_succeeded, failure=identify_failed)
   
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
      
      def handle_login_success(reply, cancel):
         def handle_fetch(reply, cancel, data):
            print "data: %s" % data
         
         self.send("fetch", "GET", "/hello-world", data=handle_fetch)
      
      def handle_login_failed(reply, cancel, error):
         print "** Login failed: %s **" % error
      
      self.send("login", "fred", "fredspassword",
       success=handle_login_success, failure=handle_login_failed)
   
   def get_user_agent(self):
      return ("Test/Python %s.%s.%s" % (sys.version_info.major,
         sys.version_info.minor, sys.version_info.micro), "(undefined)")
   
   def received_identify(self, reply):
      reply("identity", *self.get_user_agent())
   
   def received_echo(self, reply):
      reply("echo")