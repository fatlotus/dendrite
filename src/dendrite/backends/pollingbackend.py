from twisted.internet import defer, reactor
from twisted.web import client
import twisted
from urllib import urlencode
import re
import json

LOGIN_URL = "https://www.globusonline.org/authenticate"
GOST_EXTRACTOR = r">GOST\.override\((.+?)\);</script>"
SAML_EXTRACTOR = r"\Asaml=(\".+?\");"

def betterGetPage(url, contextFactory=None, post=None, *vargs, **dargs):
   """
   Code _almost_ stolen from getPage: instead, we just return the
   HTTPClientFactory for better manipulation.
   """
   
   if post is not None:
      dargs["postdata"] = urlencode(post) if post is dict else post
      if dargs.get("headers", None) is None:
         dargs["headers"] = { }
      dargs["headers"]['Content-type'] = 'application/x-www-form-urlencoded; charset=utf-8'
      if dargs.get("method", None) is None:
         dargs["method"] = "POST"
   
   if not "timeout" in dargs:
      dargs["timeout"] = 15
   
   if not "followRedirect" in dargs:
      dargs["followRedirect"] = 0
   
   scheme, host, port, path = client._parse(url)
   factory = client.HTTPClientFactory(url, *vargs, **dargs)
   if scheme == 'https':
      from twisted.internet import ssl
      if contextFactory is None:
         contextFactory = ssl.ClientContextFactory()
      reactor.connectSSL(host, port, factory, contextFactory)
   elif scheme == 'http':
      reactor.connectTCP(host, port, factory)
   else:
      raise "Invalid URL scheme: %s" % scheme
   
   return factory

def authenticate(username, password, info=None):
   f = betterGetPage(LOGIN_URL, 
      post=urlencode({'username' : username, 'password' : password}))
   
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
               return { "saml_token" : match.group(1) }
         
         raise failure
   
   f.deferred.addCallback(success)
   f.deferred.addErrback(failure)
   
   return f.deferred

class Request(object):
   def __init__(self, method, url, query_string, body):
      pass
   
   def fetch(self, success, failure):   
      # Invoke success(data) when the request completes successfully,
      # and failure(err, message) when it doesn't.
      pass
   
   def listen(self, update, failure):
      # Invoke update(type, newdata) when the resource is updated,
      # and failure(err, message) when something fails.
      pass
   
   def cancel(self):
      # Cancel the listeners, if any.
      pass