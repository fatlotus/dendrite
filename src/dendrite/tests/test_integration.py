from nose.twistedtools import deferred, reactor
from dendrite.protocol import base
from dendrite.tests.controllers import test_client
from dendrite.controllers import frontend
from dendrite.backends import stub, polling
from dendrite.storage import memory as memory_storage
from dendrite.container import memory as memory_container
from dendrite import ComponentGroup
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
def integrate(controller=None, **dargs):
   global nonce
   
   if controller is None:
      controller = frontend.Controller()
   
   if "storage_backend" not in dargs:
      dargs["storage_backend"] = memory_storage.Database()
   
   if "api_backend" not in dargs:
      dargs["api_backend"] = stub.Backend()
   
   if "service_container" not in dargs:
      dargs["service_container"] = memory_container.Container()
   
   nonce += 1
   
   filename = ("tmp/%s.sock" %
      hashlib.sha1('%s-%s' % (nonce, time.time())).hexdigest()[:20]
   )
   
   group = ComponentGroup()
   group.add(controller)
   
   for (name, component) in dargs.items():
      group.add(component, name=name)
   
   group.initialize()
   
   test_bench = test_client.Controller()
   
   server_factory = base.DendriteProtocol.build_factory(
    controller, is_initiator=False)
   
   client_factory = base.DendriteProtocol.build_factory(
    test_bench, is_initiator=True)
   
   servers.append(reactor.listenUNIX(filename, server_factory))
   clients.append(reactor.connectUNIX(filename, client_factory))
   
   return test_bench.deferred

@deferred(timeout=10.0)
@with_setup(setup, teardown)
@attr('integration')
def test_integration():
   return integrate()

@deferred(timeout=10.0)
@with_setup(setup, teardown)
@attr('integration', 'live')
def test_live_integration():
   return integrate(api_backend=polling.Backend())