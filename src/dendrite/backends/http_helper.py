from twisted.internet import defer, reactor
from twisted.web import client
from urllib import urlencode

__all__ = [ 'fetch' ]

def fetch(url, contextFactory=None, post=None, *vargs, **dargs):
   """
   Code _almost_ stolen from getPage: instead, we just return the
   HTTPClientFactory for better manipulation.
   """
   
   if post is not None:
      dargs["postdata"] = urlencode(post) if type(post) is dict else post
      if dargs.get("headers", None) is None:
         dargs["headers"] = { }
      dargs["headers"]['Content-type'] = 'application/x-www-form-urlencoded; charset=utf-8'
      if dargs.get("method", None) is None:
         dargs["method"] = "POST"
   
   if not "timeout" in dargs:
      dargs["timeout"] = 30
   
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
