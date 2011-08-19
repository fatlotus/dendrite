import stub
import logging

def instance():
   if _instance is None:
      from dendrite import storage, backends
      
      _instance = stub.Container(storage.choose_backend(), backends.choose_backend())
   
   logging.warn("Deprecated singleton factory called for container instance.")
   
   return _instance