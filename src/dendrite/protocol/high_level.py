from twisted.internet import reactor # FIXME
from dendrite import backends

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
   
   def received_login(self, reply, username, password):
      def login_succeeded(ignored):
         reply("success")
         self._authenticated = True
      
      def login_failed(err):
         reply("failure", str(err))
         self._authenticated = False
      
      d = self._backend.authenticate(username, password)
      d.addCallback(login_succeeded)
      d.addErrback(login_failed)
   
   def received_fetch(self, reply, method, url):
      if self._authenticated:
         def fetch_response(data):
            reply("data", data)
         
         def failed(err):
            reply("failure", str(err))
         
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
            print "error: %s" % repr(error)
         else:
            self.send("fetch", handle_response, "GET", "/hello-world")
      
      self.send("login", handle_authenticate, "fred", "fredspassword")
   
   def received_echo(self, reply):
      reply("echo")