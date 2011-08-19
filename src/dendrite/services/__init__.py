from dendrite.services import iphone

def choose_service_for(userAgent):
   if 'IPHONE' in userAgent.upper():
      return iphone.Service
   else:
      return None