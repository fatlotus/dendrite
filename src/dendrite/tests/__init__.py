from nose.twistedtools import reactor
import os

try:
   for filename in os.listdir("tmp/"):
      if filename.endswith(".sock"):
         os.unlink("tmp/%s" % filename)
except:
   pass