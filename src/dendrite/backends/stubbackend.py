from twisted.internet import defer

def authenticate(username, password):
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
       # This joke is no longer funny.
   return d

class Request(object):
   def __init__(self, session, method, url, query_string, body):
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
      # and failure(err, message) when something fails.
      
      self.timer = reactor.callLater(5, self._update, update)
   
   def cancel(self):
      self.timer.cancel()