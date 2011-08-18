import stub
import logging

_instance = stub

def instance():
   logging.warn("Deprecated singleton factory called for container instance.")
   
   return _instance