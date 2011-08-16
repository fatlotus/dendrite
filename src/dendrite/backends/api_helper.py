from twisted.internet import defer
from dendrite.backends import http_helper
from dendrite import storage
from dendrite import devices
import urlparse
import urllib
import json
import time

APIs = {
   "transfer" : "https://transfer.api.globusonline.org/v0.10/%s",
   "dendrite" : None # calls custom_api below.
}

def custom_api(request):
   d = defer.Deferred()
   
   if request["url"] == "dendrite/aboutme" and request["method"].upper() == "GET":
      # Returns some basic information about the current user.
      d.callback("{\"fullname\":\"Joe User\",\"email\":\"email@address.com\"}")
      
   elif request["url"] == "dendrite/background":
      # Gets and sets information about background notification.
      
      # First, we retrieve the (hopefully cached) connection
      # to the backend.
      storage_backend = storage.choose_backend()
      username = request['session']['username']
      userAgent = request['session']['userAgent']
      deviceID = request['session']['deviceID']
      device = devices.create_backend(userAgent, deviceID, storage_backend)
      
      if request["method"].upper() == "GET":
         result = storage_backend.get_notification_options(username)
         
         if result is None:
            result = device.default_options()
         
         result['enabled'] = storage_backend.is_notifying_in_background(username)
         
         d.callback(json.dumps(result))
         
      elif request["method"].upper() == "POST":
         try:
            options = json.loads(request['body'])
         except Exception:
            d.errback(Exception('Invalid JSON: %s' % repr(request['body'])))
         else:
            enabled = options['enabled']
            del options['enabled']
            
            if not device.validate_options(options):
               d.errback(Exception('Invalid options.'))
            else:
               storage_backend.set_notifies_in_background (
                 username, deviceID, enabled)
               storage_backend.set_notification_options(username, options)
               
               d.callback('{}')
   else:
      d.errback(Exception('404 File Not Found'))
   
   return d

def client_side_filtering(request):
   qs = urlparse.parse_qs(request["query_string"])
   
   for field in qs:
      qs[field] = ''.join(qs[field])
   
   client_side_filters = [ ]
   
   if "filter" in qs:
      server_side_filters = [ ]
      existing_filters = [ x.split(':') for x in qs["filter"].split('/') ]
      for key, value in existing_filters:
         if key == 'activated':
            client_side_filters.append(lambda e: e["activated"])
         else:
            server_side_filters.append( '%s:%s' % (key, value) )
      qs["filter"] = '/'.join(server_side_filters)
   
   request["query_string"] = urllib.urlencode(qs)
   
   def process(response):
      def _filter(item):
         for x in client_side_filters:
            if not x(item):
               return False
         return True
      
      def _sort():
         pass
      
      response["DATA"] = [ x for x in response["DATA"] if _filter(x) ]
      
      return response
   
   return process

overrides = {
  ('GET', "transfer/endpoint_list.json") : client_side_filtering
}

def fetch_api(request):
   # clone the request dictionary so that we can make
   # adjustments to request parameters.
   request_dict = request.__dict__.copy()
   output_filter = None
   
   # client-side filtering and sorting
   api_call = (request.method, request.url)
   if api_call in overrides:
      output_filter = overrides[api_call](request_dict)
   
   if not(output_filter):
      output_filter = lambda x: x
   
   # api-switching.
   (api_name, api_path) = request.url.split('/', 2)
   
   try:
      api = APIs[api_name]
   except KeyError:
      raise ValueError("Unknown API %s" % api_name)
   
   if api is None:
      # dendrite-local API.
      result = custom_api(request_dict)
   else:
      # HTTP[S] REST API
      url = api % str("%s?%s" % (
         urllib.quote(api_path), request_dict["query_string"]))
   
      # sending the actual request.
      f = http_helper.fetch(url,
         method=str(request_dict["method"]),
         postdata=str(request_dict["body"]),
         cookies={ "saml" : request.session.get("auth_cookie") })
   
      # post-filter hook invocation.
      result = f.deferred
   
   result.addCallback(lambda data: output_filter(json.loads(data)))
   
   return result