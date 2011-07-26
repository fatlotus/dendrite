from twisted.internet import reactor # FIXME

class ServerSideConnection():
   def heartbeat(self):
      def handle_response(name, reply, cancel):
         cancel()
      self.send("echo", handle_response)
      
      reactor.callLater(1, self.heartbeat)
   
   def received_fetch(self, reply, method, url):
      reply("data", { "worked" : True, "message" : "Server says hi!" })
   
   def initialize_connection(self):
      self.heartbeat()

class ClientSideConnection():
   def initialize_connection(self):
      def handle_response(name, reply, cancel, data):
         if name == "data":
            print "Got data: %s" % repr(data)
            
      self.send("fetch", handle_response, "GET", "/hello-world")
   
   def received_echo(self, reply):
      reply("echo")