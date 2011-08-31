from twisted.internet import defer
from dendrite import Component

class Resource(object):
   def __init__(self, auth, method, url, query_string, body):
      """
      Initialize this request given a session context and request
      information.
      """
      timer = None
   
   def _update(self, callback):
      callback('refresh', { })
      reactor.callLater(5, self._update, update)
   
   def fetch(self, success, failure):   
      # Invoke success(data) when the request completes successfully,
      # and failure(err, message) when it doesn't.
      
      success({ })
   
   def listen(self, update, failure):
      # Invoke update(type, newdata) when the resource is updated,
      # and failure(err, message) when something fails. Note that it 
      # _should not_ cancel the listener. 
      
      self.timer = reactor.callLater(5, self._update, update)
   
   def cancel(self):
      self.timer.cancel()

class Backend(Component):
   def authenticate(self, username, password):
      """
      Authenticates the user given their Globus Online username
      and password, and return a defer.Deferred. Call .errback(msg)
      with any failure message, and .callback(status) with the user
      status (as a dict).
      """
      
      d = defer.Deferred()

      if password == 'test':
         d.callback({ 'auth_cookie' : '' })
      else:
         d.errback(Exception('Identity verification failed'))
          # This pun is no longer funny because the context
          # has changed.
      return d
   
   def resource(self, *args):
      """
      Creates and initializes a resource with the specified arguments.
      
      See the Resource constructor for what these arguments are.
      """
      return Resource(*args)