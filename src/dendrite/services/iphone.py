from twisted.internet import reactor
from dendrite.services import apns_helper
import logging

# Various configuration options.
# 
# These will hopefully be refacored later into the instance
# configuration file.
#
APNS_HOST_SANDBOX = "gateway.sandbox.push.apple.com"
APNS_HOST_PRODUCTION = "gateway.push.apple.com"

APNS_HOST = APNS_HOST_SANDBOX
APNS_PORT = 2195

CLIENT_CERTIFICATE = "config/keys/apns.pem"
CLIENT_PRIVATE_KEY = "config/keys/apns.key"

# The APNs adapter "service" that runs the polling request handlers
# and push notifications. It also pools the connection to the APNs,
# so that Apple doesn't get mad at us.
class Service(object):
   
   def __init__(self, storage_backend, api_backend):
      """
      Initialize the Apple Push Notification Service adapter
      Service (quite a mouthful) with the specified backend.
      
      This method triggers a connection to the APNs service,
      and reuses that connection for all notifications.
      """
      
      # Create and initialize a connection factory of the APN
      # custom sockets procol. Since the factory is duck-typed
      # with a ssl.ClientContextFactory, we use it for both the
      # standard host and port.
      _ = apns_helper.APNProtocol.build_factory (
       CLIENT_CERTIFICATE, CLIENT_PRIVATE_KEY)
      self.connection = reactor.connectSSL(APNS_HOST, APNS_PORT, _, _)
      
      # Record the deferred for when the connection to the APNs
      # has finished. This allows us to asynchronously connect
      # and reuse a single protocol.
      self.protocol_deferred = _.deferred
      
      # Initialize the mapping of usernames to lists of requests
      # and record the backend.
      self.requests = { }
      self.api_backend = api_backend
      self.storage_backedn = storage_backend
      
      # Initialize a per-service logger.
      self.logger = logging.getLogger('APNsDaemon')
      
      self.logger.info("Inititializing APNs Service")
   
   def add(self, session):
      """
      Adds an iPhone to this service, and begins tracking transfers
      on its behalf. This requires setting up a polling backend and
      pulling data from the transfer API.
      """
      
      # Index based on the username, since GO usernames never change.
      # 
      # The assumption here is that #remove is called before the 
      # deviceID is changed for an individual user account.
      username = session['username']
      
      if username in self.requests:
         raise ValueError, "Already added session to request."
      
      # Initialize a list of requests (listeners) to handle for this
      # connection.
      
      self.requests[username] = [ ]
      
      # We're monitoring the task list in order to look for changed or
      # updated transfers via the "remove" notification type.
      task_list = self.api_backend.Request (session,
        'GET', 'transfer/task_list', 'filter=status:ACTIVE,INACTIVE', ''
      )
      
      # Create a callback for the changes in the task list. This basically
      # is just accessing the same thing as a LISTEN request, but masking
      # everything but the "remove" type.
      def task_list_notify(kind, value):
         if kind == 'remove':
            
            # A task is no longer ACTIVE or INACTIVE, so let's assume that
            # it finished.
            #
            message = 'Task %s... has completed' % value['data']['task_id'][:10]
            
            # Use this little bit of voodoo to ensure that the connection
            # has completed before triggering the notification.
            # 
            # It's an edge case, but because Twisted hates queued writes
            # (largely because of the presence of deferreds), we need
            # to do this. Most of the time, #addCallback will just call
            # the lambda directly.
            # 
            self.protocol_deferred.addCallback(
               lambda x: x.notify(session['deviceID'], alert=message))
            
         elif kind == 'refresh':
            
            # Uh oh! Everything changed! Drastically! Panic! Sorta.
            #
            # However, this is not unrecoverable: log it and ignore
            # it. We're assuming that dropped notifications are not
            # critical failures.
            # 
            self.logger.warn (
               'Received a refresh to a watched property: we might have '
               'missed a notification!'
            )
      
      # Listen to the specified task list.
      task_list.listen(task_list_notify)
      
   def remove(self, session):
      """
      Unregisters a user from the Apple Push Notification Service. This
      cleans up any push resources that the user was taking up.
      """
      
      # Index based on the person's GO username. See the discussion in
      # the method #add above regarding continuity.
      #
      username = session['username']
      
      # Cancel all polling requests for this user, which should free
      # all other resources recursively.
      # 
      for request in self.requests[username]:
         request.cancel()
      
      # Garbage collect all state.
      del self.requests[username]
   
   def validate_options(self, options):
      """
      Validates the options given to the APNs service.
      
      Right now, there are only two valid ones: "expire" and
      "sounds". Both are booleans, specifying whether credential
      expiration notifications and aural notifications are to be
      send, respectively.
      """
      return (
         len(options) == 2 and
         'expire' in options and
         'sounds' in options and
         type(options['expire']) is bool and
         type(options['sounds']) is bool
      )
   
   def default_options(self):
      """
      Returns the default set of options, send whenever the user's
      preferences are invalid or unavailable.
      """
      return {
         'expire' : True,
         'sounds' : True
      }