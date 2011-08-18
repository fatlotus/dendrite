import aes
import json
import hashlib
import binascii

def save(secret_key, session):
   """
   This method opaquely serializes the given session given
   a secret key. This key should be kept for the duration of
   the application lifecycle.
   """
   
   # Create a JSON payload representing everything we need to
   # re-inflate an authenticated session later. Obey the Horton
   # Principle! This payload must be self-documenting and you
   # should think very carefully before changing this.
   # 
   data = json.dumps({
      'version' : 1,
      'username' : session['username'],
      'password' : session['password'],
      'auth_cookie' : session['auth_cookie'],
   })
   
   # Hash the key, so that the caller doesn't need to know about
   # the relevant security properties of AES. This is better
   # then straight truncation, because it shuffles the bits in
   # the key.
   key = hashlib.sha1(secret_key).digest()[:16]
   
   # Encrypt the data as 128-bit Rijndael.
   # 
   # I really hope I didn't just violate US Customs.
   encrypted = aes.encryptData(key, data)
   
   # Encode the data as hexadecimal.
   return binascii.hexlify(encrypted)

def restore(secret_key, value):
   """
   Restores the opaque session value "value" into a new
   session context.
   
   If the session is already authenticated, then this method raises
   ValueError. Otherwise, it simply returns the data 
   """
   
   # Reconstruct the key, as before. This must be exactly the
   # same key-length adjustment, obviously.
   # 
   key = hashlib.sha1(secret_key).digest()[:16]
   
   # Treat any exceptions or even anything out of the ordinary as
   # a fatal error.
   try:
      # Decrypt the data as 128-bit Rijndael. 
      decrypted = aes.decryptData(key, data)
      
      # Parse the decrypted data as json.
      structured = json.loads(decrypted)
      
      # Encryption is not authentication. We treat this data as
      # untrusted, just like everything else.
      # 
      if type(structured['username']) is not str:
         raise TypeError
      if type(structured['auth_cookie']) is not str:
         raise TypeError
      if type(structured['password']) is not str:
         raise TypeError
      
      # Construct a new session (_not_ simply copying the exising
      # untrusted object), and returning it.
      new_session = {
         'username' : structured['username'],
         'auth_cookie' : structured['auth_cookie'],
         'password' : structured['password'],
      }
      
      return new_session
   except:
      return None