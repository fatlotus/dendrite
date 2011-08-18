import memory
import logging

instance = memory.Database()

def choose_backend():
   logging.warn("Backend selection should not be via singletons.")
   return instance