class Service(object):
   def __init__(self, storageBackend):
      pass
   
   def validate_options(self, options):
      return (
         len(options) == 1 and
         'color' in options and
         options['color'] in ('blue', 'red')
      )
   
   def default_options(self):
      return {
         'color' : 'blue',
      }