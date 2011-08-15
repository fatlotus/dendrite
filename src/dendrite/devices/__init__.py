import iphone

def create_backend(userAgent, deviceID, storageBackend):
   if 'IPHONE' in userAgent.upper():
      return iphone.Device(deviceID, storageBackend)