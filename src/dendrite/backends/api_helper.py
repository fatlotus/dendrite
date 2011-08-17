from twisted.internet import defer
from dendrite.backends import http_helper
from dendrite import storage
from dendrite import services
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
      service = devices.create_service_for(request['session'], storage_backend)
      
      if request["method"].upper() == "GET":
         # If we're GETTING the background information, then 
         # ask the storage layer first.
         result = storage_backend.get_notification_options(username)
         
         # If not, fallback to the service's defaults.
         if result is None:
            result = service.default_options()
         
         # Either way, set the "enabled" key to whatever the
         # storage layer wants.
         result['enabled'] = storage_backend.is_notifying_in_background(username)
         
         d.callback(json.dumps(result))
         
      elif request["method"].upper() == "POST":
         try:
            options = json.loads(request['body'])
         except Exception:
            d.errback(Exception('Invalid JSON: %s' % repr(request['body'])))
         else:
            # We're pulling the 'enabled' option out of the
            # notifications settings because that's almost a
            # meta-attribute: it defines whether the other 
            # attributes are useful.
            # 
            # They must still be stored, however, since those
            # attributes should still be considered
            # "preferences" for the service.
            # 
            enabled = options.pop('enabled')
            
            # Run all validation in a service-specific manner.
            if not service.validate_options(options):
               d.errback(Exception('Invalid options.'))
            else:
               # Store all data against the server.
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