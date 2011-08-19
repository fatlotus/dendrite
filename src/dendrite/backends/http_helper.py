from twisted.internet import defer, reactor
from twisted.web import client
from urllib import urlencode

__all__ = [ 'fetch' ]

def fetch(url, contextFactory=None, post=None,
 timeout=5, headers={ }, *vargs, **dargs):
   """
   Performs a URL fetch on the given URL given a dictionary of form
   fields in the post array.
   
   Code _almost_ stolen from getPage: instead, we just return the
   HTTPClientFactory for better manipulation.
   """
   
   if post is not None:
      
      # If we're POSTing data, then urlencode it if necessary.
      # 
      dargs["postdata"] = urlencode(post) if type(post) is dict else post
      
      # Enable a POST-form-data content-type.
      headers['Content-type'] = (
       'application/x-www-form-urlencoded; charset=utf-8'
      )
      
      # Ensure that the request method, if not already specified,
      # is POST.
      if dargs.get("method", None) is None:
         dargs["method"] = "POST"
   
   dargs['timeout'] = timeout
   dargs['headers'] = headers
   
   (scheme, host, port, path) = client._parse(url)
   
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
