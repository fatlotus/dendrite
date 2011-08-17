from twisted.internet import reactor
from dendrite.protocol import base
from dendrite.tests.controllers import test_client
from dendrite.controllers import frontend
from dendrite.backends import stubbackend
from nose.tools import *
from nose.plugins.attrib import attr

_test_client = None
_frontend = None

def setup():
   global _test_client, _frontend
   
   _test_client = test_client.Controller(shutdown)
   _frontend = frontend.Controller(stubbackend)

def shutdown(error=None):
   try:
      reactor.stop()
   except:
      pass
   
   if error:
      fail(error)

def teardown():
   global _test_client, _frontend
   
   _test_client = None
   _frontend = None
   
   shutdown()

@nottest
def integration_test(a, b):
   facA = base.DendriteProtocol.build_factory(a, is_initiator=True)
   facB = base.DendriteProtocol.build_factory(b, is_initiator=False)
   
   reactor.listenUNIX('tmp/integration_tests.sock', facB)
   reactor.connectUNIX('tmp/integration_tests.sock', facA)
   reactor.callLater(10, shutdown, 'Test timed out.')
   
   reactor.run()

@istest
@attr('integration')
def test_integration():
   integration_test(_test_client, _frontend)