from twisted.internet import reactor
from dendrite.protocol import base
from dendrite.tests.controllers import test_client
from dendrite.controllers import frontend
from dendrite.backends import stubbackend, pollingbackend
from nose.tools import *
from nose.plugins.attrib import attr

servers = [ ]
clients = [ ]
timers = [ ]

@nottest
def teardown():
   for client in clients:
      client.disconnect()
   
   for server in servers:
      server.stopListening()
   
   for timer in timers:
      timer.cancel()
   
   try:
      reactor.stop()
   except:
      pass

@nottest
def shutdown(reason=None):
   teardown()
   
   print repr(reason)

@nottest
def integration_test(a, b):
   facA = base.DendriteProtocol.build_factory(a, is_initiator=True)
   facB = base.DendriteProtocol.build_factory(b, is_initiator=False)
   
   servers.append(reactor.listenUNIX('tmp/integration_tests.sock', facB))
   clients.append(reactor.connectUNIX('tmp/integration_tests.sock', facA))
   timers.append(reactor.callLater(20, shutdown, 'Test timed out.'))
   
   reactor.run()

@istest
@attr('integration')
def test_integration():
   integration_test(test_client.Controller(), frontend.Controller(stubbackend))

# # Here there be monsters:
# 
# @istest
# @attr('live-integration')
# def test_live_integration():
#    integration_test(test_client.Controller(), frontend.Controller(pollingbackend))