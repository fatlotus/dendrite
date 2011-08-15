def create_backend(userAgent, deviceID, storageBackend):
   if 'iPhone' in userAgent:
      return iphone.Device(deviceID, storageBackend)