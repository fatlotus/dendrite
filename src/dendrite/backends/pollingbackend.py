from twisted.internet import defer, reactor
from twisted.web import client
import twisted
from urllib import urlencode
import re
import json

LOGIN_URL = "https://www.globusonline.org/authenticate"
API_CALL = "https://transfer.api.globusonline.org/v0.10/%s"
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
      dargs["timeout"] = 10
   
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
      raise Exception("Invalid URL scheme: %s" % scheme)
   
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
               return { "auth_cookie" : match.group(1) }
         
   
   f.deferred.addCallback(success)
   f.deferred.addErrback(failure)
   
   return f.deferred

class Request(object):
   def __init__(self, session, method, url, query_string, body):
      self.session = session
      self.method = method
      self.url = url
      self.query_string = query_string
      self.body = body
      self.cancelled = False
   
   def fetch(self, success, failure):
      print "URL: %s" % (API_CALL % str("%s?%s" % (self.url, self.query_string)))
      f = betterGetPage(API_CALL % str("%s?%s" % (self.url, self.query_string)),
         method=str(self.method),
         postdata=str(self.body),
         cookies={ "saml" : self.session.get("auth_cookie") })
      f.deferred.addCallback(lambda body: success(json.loads(body)))
      f.deferred.addErrback(lambda f: failure("RequestFailed", f.getErrorMessage()))
   
   def listen(self, update, failure):
      def set_initial_content(content):
         def differencing(body):
            if body != content:
               update("refresh", body)
               set_initial_content(body)
            elif not self.cancelled:
               reactor.callLater(30.0, set_initial_content, content)
         self.fetch(differencing, failure)
      
      self.fetch(set_initial_content, failure)
   
   def cancel(self):
      self.cancelled = True