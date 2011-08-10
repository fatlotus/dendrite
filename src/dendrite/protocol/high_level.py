from twisted.internet import reactor # FIXME
from dendrite import backends
import sys

class ServerSideConnection():
   def initialize_connection(self):
      self.startTLS(is_server=True)
      self.heartbeat()
      self._backend = backends.preferred()
      self._session = None
      self._closed = False
      self._listeners = [ ]
   
   def terminate_connection(self):
      for listener in self._listeners:
         listener.cancel()
      self._closed = True
   
   def is_authenticated(self):
      return (self._session != None)
   
   def heartbeat(self):
      if self._closed:
         return
      
      def handle_response(reply, cancel):
         pass
      self.send("echo", echo=handle_response)
      
      reactor.callLater(30, self.heartbeat)
   
   def received_session(self, reply_to_session):
      reply_to_session("data", self._session)
   
   def received_login(self, reply_to_login, username, password):
      def try_authenticate(userAgent):
         def login_succeeded(result):
            if not self.is_authenticated():
               reply_to_login("success")
               self._session = result
         
         def login_failed(err):
            reply_to_login("failure", "LoginFailed", err.getErrorMessage())
            self._session = None
         
         d = self._backend.authenticate(username, password, info=userAgent)
         d.addCallback(login_succeeded)
         d.addErrback(login_failed)
      
      def identify_succeeded(reply, cancel, userAgent, deviceID):
         try_authenticate(userAgent)
      
      def identify_failed(reply, cancel, err):
         try_authenticate("(unknown)")
      
      try_authenticate("none")
      self.send("identify", identity=identify_succeeded,
         failure=identify_failed)
   
   def received_fetch(self, reply, method, url, query_string, body):
      if self.is_authenticated():
         def success(data):
            if self.is_authenticated():
               reply('data', data)
         
         def failure(failure, desc):
            if self.is_authenticated():
               reply('failure', failure, desc)
         
         self._backend.Request(self._session, method, url, query_string,
            body).fetch(success, failure)
      else:
         reply("failure", "AuthRequired", "The fetch command requires authentication.")
   
   def received_listen(self, reply_to_listen, url, query_string):
      if self.is_authenticated():
         request = self._backend.Request(self._session, 'GET', url, query_string, '')
         
         self._listeners.append(request)
         
         def handle_cancel(reply_to_cancel, keep_waiting):
            request.cancel()
      
         def got_new_data(*data):
            if self.is_authenticated():
               reply_to_listen("notify", *data, cancel=handle_cancel)
      
         def request_failed(*info):
            if self.is_authenticated():
               reply_to_listen("failure", *info)
      
         request.listen(got_new_data, request_failed)
      
         reply_to_listen("success", cancel=handle_cancel)
      else:
         reply_to_listen("failure", "AccessDenied", "Cannot Listen without authentication.")
   

class ClientSideConnection():
   def initialize_connection(self):
      self.startTLS(is_server=False)
      
      def handle_login_success(reply, keep_waiting):
         def handle_successful_listen(reply, keep_waiting):
            keep_waiting()
         
         def handle_notify(reply_to_notify, keep_waiting, notification_type, data):
            keep_waiting()
         
         def handle_data(reply_to_data, keep_waiting, data):
            pass
         
         self.send("fetch", "GET", "task_list", "", "",
          success=handle_successful_listen, data=handle_data)
         
         self.send("listen", "task_list", "",
          success=handle_successful_listen, notify=handle_notify)
      
      def handle_login_failed(reply, keep_waiting, error, description):
         print "** Login failed: %s **" % description
      
      self.send("login", "fatlotus", "test",
       success=handle_login_success, failure=handle_login_failed)
   
   def get_user_agent(self):
      return ("Test/Python %s.%s.%s" % (sys.version_info.major,
         sys.version_info.minor, sys.version_info.micro), "(undefined)")
   
   def received_identify(self, reply):
      reply("identity", *self.get_user_agent())
   
   def received_echo(self, reply):
      reply("echo")