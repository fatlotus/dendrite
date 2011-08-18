class Service(object):
   def __init__(self, storageBackend):
      """
      Initialize this service given a storage backend. Each Service
      instance processes many clients at a time, to take advantage
      of multiplexed streams and parallel connections.
      """
   
   def add(self, session):
      """
      Start running a service on behalf of the specified 'session'
      context. If you wish to get the notification options, you'll
      need to fetch the options from the storage backend.
      """
   
   def remove(self, session):
      """
      Stop the service for 'session' in the background, asynchronously.
      
      This method should mask any further callbacks as soon as possible and
      clean up any resources used.
      """
   
   def shutdown(self):
      """
      Cancels this service. When a service is cancelled, all clients
      should be automatically removed from it.
      """
   
   def validate_options(self, options):
      """
      Validates the set of options, returning True if
      the options are valid, and False if they aren't.
      
      These options passed-in will be entirely user-
      facing: anything valid in JSON will be valid here.
      
      This stub service accepts a single required attribute
      "color" which can either be "blue" or "red".
      """
      return (
         type(options) is dict and
         len(options) == 1 and
         'color' in options and
         options['color'] in ('blue', 'red')
      )
   
   def default_options(self):
      """
      Returns the default option set. This hopefully passes
      the validation exposed in .validate_options( ) above.
      
      This stub service defaults to the 'color' of 'blue'.
      """
      return {
         'color' : 'blue',
      }