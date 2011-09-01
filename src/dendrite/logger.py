import logging
import threading

state = threading.local()

def initialize():
   state.context = ''
   
   class Filter(object):
      def filter(self, record):
         record.msg = '%s%s' % (state.context, record.msg)
         return True
   
   logging.getLogger().addFilter(Filter())

def with_context(context, block, *args, **dargs):
   if not hasattr(state, 'context'):
      initialize()
   
   old_context = state.context
   state.context = '%s%s: ' % (old_context, context) 
   
   try:
      block(*args, **dargs)
   finally:
      state.context = old_context