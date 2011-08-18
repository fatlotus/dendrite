import logging
import pollingbackend

instance = pollingbackend

def choose_backend():
   logging.warn("Use of singleton selectors is deprecated.")
   return instance