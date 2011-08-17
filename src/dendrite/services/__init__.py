import iphone

def background_service_for(session, storageBackend):
   userAgent = session['userAgent']
   deviceID = session['deviceID']
   
   if 'IPHONE' in userAgent.upper():
      return iphone.Device(session, storageBackend)