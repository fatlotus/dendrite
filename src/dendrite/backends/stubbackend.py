def authenticate(username, password):
   # Return a defer.Deferred. Call .errback(msg) with any failure message,
   # and .callback(status) with the user status (as a dict).
   
   pass

class Request(object):
   def __init__(self, session, method, url, query_string, body):
      pass
   
   def fetch(self, success, failure):   
      # Invoke success(data) when the request completes successfully,
      # and failure(err, message) when it doesn't.
      pass
   
   def listen(self, update, failure):
      # Invoke update(type, newdata) when the resource is updated,
      # and failure(err, message) when something fails.
   
   def cancel(self):
      # Cancel the listeners, if any.