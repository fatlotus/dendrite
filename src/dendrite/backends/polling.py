from twisted.internet import defer, reactor
import twisted
import re
import json
from dendrite.backends import http_helper
import dendrite.diff
import dendrite.storage
from dendrite import container, Component, services
import sys
import logging

LOGIN_URL = "https://www.globusonline.org/authenticate"
GOST_EXTRACTOR = r">GOST\.override\((.+?)\);</script>"
SAML_EXTRACTOR = r"\Asaml=(\".+?\");"

POLL_DELAY = 10

APIs = {
   "transfer" : "https://transfer.api.globusonline.org/v0.10/%s"
}

class Resource(object):
   def __init__(self, component, auth, method, url, query_string, body):
      """
      Initialize this resource given a source authentication
      context and REST request.
      """
      self.component = component
      self.auth = auth
      self.method = method.upper()
      self.url = url
      self.query_string = query_string
      self.body = body
      self.output_filter = None
      self.api = None
      self.cancelled = False
   
   def fetch(self, success, failure):
      """
      Sends this request, taking in to account any of the current
      request overlays and adjustments we need to make to "fix"
      some of the dearth of features in the Transfer API.
      """
      d = defer.Deferred()
      
      if self.url == "dendrite/aboutme" and self.method == "GET":
         # Returns some basic information about the current user.
         d.callback({ 'fullname' : "Joe User", 'email' : "email@address.com"})
         
      elif self.url == "dendrite/background":
         # Gets and sets information about background notification.
      
         # First, we retrieve the (hopefully cached) connection
         # to the backend.
         storage_backend = self.component.storage_backend
         username = self.auth['username']
         user_agent = self.auth['user_agent']
         device_id = self.auth['device_id']
         service_container = self.component.service_container
         service = service_container.service(services.choose_service_for(user_agent))
         device = (user_agent, device_id)
         
         if self.method == "GET":
            # If we're GETTING the background information, then 
            # ask the storage layer first.
            result = storage_backend.get_notification_options(username)
            
            # If not, fallback to the service's defaults.
            if result is None:
               result = service.default_options()
         
            # Either way, set the "enabled" key to whatever the
            # storage layer wants.
            result['enabled'] = storage_backend.is_notifying_in_background (
               username, device
            )
            
            d.callback(result)
         
         elif self.method == "POST":
            try:
               options = json.loads(self.body)
            except Exception:
               d.errback(Exception('Invalid JSON.'))
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
                    username, device, enabled)
                  storage_backend.set_notification_options(username, options)
               
                  if enabled:
                     service.add(self.auth)
                  else:
                     service.remove(self.auth)
               
                  d.callback({ })
      else:
         # Split the URL and attempt to determine
         # which API the end-user is requesting.
         #
         (api_name, remainder) = self.url.split('/', 1)
         
         # Calculate the full URL from the API name
         # and suffix.
         full_url = (APIs[api_name] % remainder)
         
         # The assumption here is that any data send over
         # Dendrite is encoded as form variables. Hopefully,
         # the API doesn't need this! 
         headers = { }
         
         if self.method != 'GET':
            headers['Content-type'] = (
             'application/x-www-form-urlencoded; charset=utf-8'
            )
         
         # Add the overlay auth_token value to ensure proper
         # authentication.
         headers['Cookie'] = 'saml=%s' % self.auth['auth_cookie']
         
         # Perform the actual HTTP fetch operation.
         d = http_helper.fetch(
            url=str(full_url),
            method=str(self.method),
            postdata=str(self.body),
            headers=headers
         ).deferred
         
         d.addCallback(lambda body: json.loads(body))
      
      # Trigger success() and failure() on the result of
      # the deferred.
      d.addCallback(lambda body: success(body))
      
      def _failure(f):
         logging.error("Request failed: %s" % f.getErrorMessage())
         failure("RequestFailed", f.getErrorMessage())
      
      d.addErrback(_failure)
   
   def listen(self, update, failure):
      def cancel_and_fail(*args):
         self.cancel()
         failure(*args)
         
      def set_initial_content(content):
         def differencing(body):
            changes = dendrite.diff.diff(content, body)
            
            if not self.cancelled:
               for (kind, data) in changes:
                  update(kind, data)
               
               reactor.callLater(POLL_DELAY, set_initial_content, content)
         self.fetch(differencing, failure)
      
      self.fetch(set_initial_content, failure)
   
   def cancel(self):
      self.cancelled = True

class Backend(Component):
   def authenticate(self, username, password):
      """
      Attempts to authenticate via the Globus Online web form by passing
      the username and password as form parameters.
      """
      
      # Trigger the HTTP helper to make the request.
      #
      # We disable HTTP redirects because it makes things somewhat
      # simpler. If there is an HTTP "error," then we treat it as
      # a success because that's actually a redirect.
      #
      f = http_helper.fetch(LOGIN_URL, followRedirect=0,
         post={'username' : username, 'password' : password})
      
      def success(body):
         # A "successful" request is actually a failure, as it
         # means that the login page has returned an error
         # response.
         match = re.search(GOST_EXTRACTOR, body, re.MULTILINE)
         message = "Invalid username or password."
         
         # Try to figure out the error message, if possible.
         # 
         # If this fails for any reason, then simply fail
         # silently.
         if match is not None:
            try:
               # Attempt to parse the GOST as pure JSON, and
               # extract the error message as a kluge.
               data = json.loads(match.group(1))
               message = data['preload'][0]['content']['errors'][0]['message']
            except:
               logging.warn (
                'Unable to parse the given GOST packet from the '
                'response: perhaps GOST has updated incompatibly?'
               )
         else:
            logging.warn (
             'Unable to extract a GOST packet from the response: '
             'perhaps GOST has updated incompatibly?'
            )
         
         # Switch a failure to a success.
         raise ValueError(message)
      
      def failure(failure):
         # Failures are actually successes, if they are redirects.
         # 
         # We're using the silly try: except: block because it
         # basically covers the really bad typed testing that's
         # in use here.
         try:
            failure.raiseException()
         except twisted.web.error.PageRedirect:
            
            # Attempt to extract all possible cookies, and try to
            # extract the SAML token. If we return None, then 
            # Twisted just keeps passing it forward, which is exactly
            # what we want.
            for cookie in f.response_headers.get("set-cookie", []):
               
               # Attempt to extract the SAML token as a regex.
               # As before, if the match is None, then skip it.
               match = re.match(SAML_EXTRACTOR, cookie)
               if match is not None:
                  # Create the authentication context and return it.
                  auth = {
                     'auth_cookie' : match.group(1),
                     'username' : username,
                     'password' : password,
                     'user_agent' : None,
                     'device_id' : None,
                  }
                  
                  return auth
         
      # Register the callbacks on the response's deferred.
      f.deferred.addCallback(success)
      f.deferred.addErrback(failure)
      
      # Return the deferred itself.
      return f.deferred
   
   def resource(self, *args):
      """
      Create and return a Resource instance. The arguments are
      the same as with the Resource constructor.
      """
      return Resource(self, *args)