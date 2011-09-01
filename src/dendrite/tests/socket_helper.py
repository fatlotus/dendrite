import time
import hashlib

nonce = 0

def generate_test_socket():
   global nonce
   
   nonce += 1
   
   filename = ("tmp/%s.sock" %
      hashlib.sha1('%s-%s' % (nonce, time.time())).hexdigest()[:20]
   )
   
   return filename