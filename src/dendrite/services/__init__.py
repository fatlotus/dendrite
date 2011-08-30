from dendrite.services import iphone

def choose_service_for(userAgent):
   """
   Chooses the backend service for the specified user-agent string.
   
   >>> from dendrite import services
   >>> services.choose_service_for('iPhone')
   <class 'dendrite.services.iphone.Service'>
   >>> services.choose_service_for('xx iphone xx')
   <class 'dendrite.services.iphone.Service'>
   >>> services.choose_service_for('xx Android xx')
   >>>
   """
   if 'IPHONE' in userAgent.upper():
      return iphone.Service
   else:
      return None