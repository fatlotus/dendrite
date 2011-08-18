from nose.twistedtools import reactor, deferred
from dendrite.protocol import base
from dendrite.tests.controllers import test_client
from dendrite.controllers import frontend
from dendrite.backends import stubbackend, pollingbackend
from dendrite.storage import memory
from nose.tools import *
from nose.plugins.attrib import attr
import os
import time

servers = [ ]
clients = [ ]
timers = [ ]

def setup():
   try:
      os.unlink('tmp/integration_tests.sock')
   except:
      pass

def teardown():
   for client in clients:
      try:
         client.disconnect()
      except:
         pass
   
   time.sleep(1)
   
   for server in servers:
      try:
         server.loseConnection()
      except:
         pass
   
   time.sleep(1)
   
   try:
      os.unlink('tmp/integration_tests.sock')
   except OSError:
      pass

@nottest
def integrate(a, b):
   nonce = time.time()
   
   facA = base.DendriteProtocol.build_factory(a, is_initiator=True)
   facB = base.DendriteProtocol.build_factory(b, is_initiator=False)
   
   servers.append(reactor.listenUNIX('tmp/integration_test.sock', facB))
   clients.append(reactor.connectUNIX('tmp/integration_test.sock', facA))
   
   return a.deferred

@deferred(timeout=10.0)
@with_setup(setup, teardown)
@attr('integration')
def test_integration():
   return integrate(test_client.Controller(), frontend.Controller(memory.Database, stubbackend))

@deferred(timeout=10.0)
@with_setup(setup, teardown)
@attr('integration', 'live')
def test_live_integration():
   return integrate(test_client.Controller(), frontend.Controller(memory.Database, pollingbackend))