from nose.twistedtools import reactor, deferred
from dendrite.protocol import base
from dendrite.tests.controllers import test_client
from dendrite.controllers import frontend
from dendrite.backends import stubbackend, pollingbackend
from dendrite.storage import memory
from nose.tools import *
from nose.plugins.attrib import attr
import time
import hashlib

servers = [ ]
clients = [ ]
timers = [ ]

nonce = 0

def setup():
   pass

def teardown():
   for client in clients:
      try:
         client.disconnect()
      except:
         pass
   
   for server in servers:
      try:
         server.loseConnection()
      except:
         pass

@nottest
def integrate(a, b):
   global nonce
   
   nonce += 1
   
   filename = ("tmp/%s.sock" %
      hashlib.sha1('%s-%s' % (nonce, time.time())).hexdigest()[:20]
   )
   
   facA = base.DendriteProtocol.build_factory(a, is_initiator=True)
   facB = base.DendriteProtocol.build_factory(b, is_initiator=False)
   
   servers.append(reactor.listenUNIX(filename, facB))
   clients.append(reactor.connectUNIX(filename, facA))
   
   return a.deferred

@deferred(timeout=10.0)
@with_setup(setup, teardown)
@attr('integration')
def test_integration():
   return integrate(test_client.Controller(), frontend.Controller(stubbackend, memory.Database))

@deferred(timeout=10.0)
@with_setup(setup, teardown)
@attr('integration', 'live')
def test_live_integration():
   return integrate(test_client.Controller(), frontend.Controller(pollingbackend, memory.Database))