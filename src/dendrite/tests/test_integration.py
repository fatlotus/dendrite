from twisted.internet import reactor
from dendrite.protocol import base
from dendrite.tests.controllers import test_client
from dendrite.controllers import frontend
from dendrite.backends import stubbackend
import unittest

class IntegrationTests(unittest.TestCase):
   def setUp(self):
      self.test_client = test_client.Controller(self)
      self.frontend = frontend.Controller(stubbackend)
   
   def tests_complete(self, error=None):
      try:
         reactor.stop()
      except:
         pass
      
      if error:
         self.fail(error)
   
   # a is the initiator.
   def integration_test(self, a, b):
      facA = base.DendriteProtocol.build_factory(a, is_initiator=True)
      facB = base.DendriteProtocol.build_factory(b, is_initiator=False)
      
      reactor.listenUNIX('tmp/integration_tests.sock', facB)
      reactor.connectUNIX('tmp/integration_tests.sock', facA)
      reactor.callLater(10, self.tests_complete, 'Test timed out.')
      
      reactor.run()
      
   
   def test_all(self):
      self.integration_test(self.test_client, self.frontend)