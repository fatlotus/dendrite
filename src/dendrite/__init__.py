class Component(object):
   """
   Pseudo-interface (more like a mixin) for a "component" of
   the Dendrite server system. Each component gets a
   reference to all the other components, by using a
   standardized referencing system.
   
   Basically, there are four main attributes:
   
   "storage_backed," for dendrite.storage.-.Database.
   "api_backend," for dendrite.backends.-.Backend
   "service_container," for dendrite.services.-.Service
   
   """
   
   storage_backend = None
   api_backend = None
   service_container = None
   
   def initialize(self):
      """
      Override this method to "initialize" this component
      when the reference attributes are set.
      """

class ComponentGroup(object):
   """
   A collection of components. This is basically just a
   standardized way of initializing a whole slew of
   interfaced services.
   """
   
   def __init__(self):
      """
      Initialize this ComponentGroup. This does not add
      services automatically, so you need to call #add.
      """
      self.components = [ ]
      self.instance_variables = { }
   
   def add(self, component, name=None):
      """
      Adds a component to this ComponentGroup, identified
      by the instance variable name "name".
      """
      self.components.append(component)
      
      if name is not None:
         self.instance_variables[name] = component
   
   def initialize(self):
      """
      Initializes all components in this ComponentGroup.
      """
      
      for (name, value) in self.instance_variables.items():
         for component in self.components:
            setattr(component, name, value)
      
      for component in self.components:
         component.initialize()