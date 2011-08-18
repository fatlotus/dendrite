from twisted.internet import defer, reactor
import twisted
import re
import json
import api_helper
import http_helper
import dendrite.diff
import dendrite.storage
from dendrite import container
import sys

LOGIN_URL = "https://www.globusonline.org/authenticate"
GOST_EXTRACTOR = r">GOST\.override\((.+?)\);</script>"
SAML_EXTRACTOR = r"\Asaml=(\".+?\");"

POLL_DELAY = 10

def authenticate(username, password):
   f = http_helper.fetch(LOGIN_URL, 
      post={'username' : username, 'password' : password})
   
   def success(body):
      match = re.search(GOST_EXTRACTOR, body, re.MULTILINE)
      message = "Invalid username or password."
      
      if match is not None:
         try:
            data = json.loads(match.group(1))
            message = data['preload'][0]['content']['errors'][0]['message']
         except Exception, e:
            pass
      else:
         pass
      
      raise ValueError(message)
   
   def failure(failure):
      try:
         failure.raiseException()
      except twisted.web.error.PageRedirect:   
         for cookie in f.response_headers.get("set-cookie", []):
            match = re.match(SAML_EXTRACTOR, cookie)
            if match is not None:
               return {
                  'auth_cookie' : match.group(1),
                  'username' : username,
                  'password' : password,
                  'storage_backend' : dendrite.storage.choose_backend(),
                  'api_backend' : sys.modules[__name__],
                  'container' : container.instance(),
                  'user_agent' : None,
                  'device_id' : None,
               }
         
   
   f.deferred.addCallback(success)
   f.deferred.addErrback(failure)
   
   return f.deferred

class Request(object):
   def __init__(self, session, method, url, query_string, body):
      self.session = session
      self.method = method.upper()
      self.url = url
      self.query_string = query_string
      self.body = body
      self.cancelled = False
   
   def fetch(self, success, failure):
      d = api_helper.fetch_api(self)
      d.addCallback(lambda body: success(body))
      d.addErrback(lambda f: failure("RequestFailed", f.getErrorMessage()))
   
   def listen(self, update, failure):
      def set_initial_content(content):
         def differencing(body):
            changes = dendrite.diff.diff(content, body)
            
            for (kind, data) in changes:
               update(kind, data)
            
            if not self.cancelled:
               reactor.callLater(POLL_DELAY, set_initial_content, content)
         self.fetch(differencing, failure)
      
      self.fetch(set_initial_content, failure)
   
   def cancel(self):
      self.cancelled = True