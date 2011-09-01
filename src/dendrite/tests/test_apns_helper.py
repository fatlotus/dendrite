from nose.twistedtools import deferred, reactor
from twisted.internet import defer
from dendrite.tests import socket_helper
from dendrite.tests.stubs import stub_apns
from dendrite.services import apns_helper

def when_connected(stub, connection):
   stub.apns = connection
   connection.notify('decafbad', badge=4, alert='Hello, there!', sound='NSFartSound')

def finished_stage1(stub):
   stub.apns.notify('decafbad', badge=5, alert=stub_apns.FAILURE_CODE)

@deferred(timeout=10)
def test_apns_integration():
   filename = socket_helper.generate_test_socket()
   
   stub = stub_apns.Service()
   apns = apns_helper.APNProtocol.build_factory(None, None)
   
   apns.deferred.addCallback(lambda x: when_connected(stub, x)) 
   apns.deferred.addErrback(lambda x: stub.stages[2].errback(x))
   
   stub.stages[1].addCallback(lambda x: finished_stage1(stub))
   
   server = reactor.listenUNIX(filename, stub)
   client = reactor.connectUNIX(filename, apns)
   
   overall = defer.DeferredList(stub.stages, fireOnOneErrback=True)
   overall.addBoth(lambda x: client.disconnect() and server.loseConnection())
   return overall