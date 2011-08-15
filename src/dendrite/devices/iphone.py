from twisted.internet import reactor

class Device(object):
   def __init__(self, deviceID, storageBackend):
      pass
   
   def poll(self):
      pass
   
   def validate_options(self, options):
      return (
         len(options) == 2 and
         'expire' in options and
         'sounds' in options and
         type(options['expire']) is bool and
         type(options['sounds']) is bool
      )
   
   def default_options(self):
      return {
         'expire' : True,
         'sounds' : True
      }