class Container():
   def __init__(self, storageBackend, apiBackend):
      """
      Initializes this ServiceContainer, given a storage
      backend. This container can be considered full of
      all of all possible services at instantiation, even
      if the actual implementation lazy-loads them.
      """
      self.services = { }
      self.storageBackend = storageBackend
      self.apiBackend = apiBackend
   
   def service(self, klass):
      """
      Returns the service of the specified class from this
      container. The returned service is initialized and
      running.
      """
      
      # If we haven't already initialized this service,
      # then lazily do so and store it.
      #
      if klass in self.services:
         self.services[klass] = klass(self.storageBackend, self.apiBackend)
      
      # Return the cached instance object.
      return self.services[klass]