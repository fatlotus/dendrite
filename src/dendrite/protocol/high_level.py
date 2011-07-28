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
      
      self.send("identify", identity=identify_succeeded,
       failure=identify_failed)
   
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
   
   def received_listen(self, reply_to_listen, method, url):
      upstream_cancel = None
      
      def handle_cancel(reply_to_cancel, keep_waiting):
         upstream_cancel()
      
      def got_new_data(notification_type, data):
         reply_to_listen("notify", notification_type, data, cancel=handle_cancel)
      
      reply_to_listen("success", cancel=handle_cancel)
      upstream_cancel = self._backend.listen(method, url, '', '', got_new_data)
   

class ClientSideConnection():
   def initialize_connection(self):
      self.startTLS(is_server=False)
      
      def handle_login_success(reply, keep_waiting):
         def handle_successful_listen(reply, keep_waiting):
            keep_waiting()
         
         def handle_notify(reply_to_notify, keep_waiting, notification_type, data):
            if data.get("count", 0) >= 5:
               print "Sending a cancel message-"
               reply_to_notify("cancel")
            else:
               print "%s: %s" % (notification_type, data)
               keep_waiting()
         
         self.send("listen", "GET", "/hello-world",
          success=handle_successful_listen, notify=handle_notify)
         
         self.send("listen", "GET", "/hello-world-2",
          success=handle_successful_listen, notify=handle_notify)
      
      def handle_login_failed(reply, keep_waiting, error):
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