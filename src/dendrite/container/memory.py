from dendrite import Component

class Container(Component):
   def __init__(self):
      """
      Initializes this ServiceContainer.
      
      This container can be considered full of
      all of all possible services at instantiation, even
      if the actual implementation lazy-loads them.
      """
      self.services = { }
   
   def service(self, klass):
      """
      Returns the service of the specified class from this
      container. The returned service is initialized and
      running.
      """
      
      # If we haven't already initialized this service,
      # then lazily do so and store it.
      #
      if klass not in self.services:
         self.services[klass] = klass(self.storage_backend, self.api_backend)
      
      # Return the cached instance object.
      return self.services[klass]