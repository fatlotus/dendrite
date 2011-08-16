from twisted.internet import reactor
import unittest
from dendrite.protocol import base
from dendrite.tests.controllers import test_client

class IntegrationTests(unittest.TestCase):
   def setUp(self):
      self.test_client = test_client.Controller(self)
      
   def tearDown(self):
      try:
         reactor.stop()
      except:
         pass
   
   def test_real_server(self):
      fac = base.DendriteProtocol.build_factory(self.test_client, is_initiator=True)
      
      reactor.connectSSL('heuristic.ci.uchicago.edu', 1337, fac, fac)
      
      reactor.run()