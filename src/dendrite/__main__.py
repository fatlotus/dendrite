import dendrite
from twisted.internet import reactor

reactor.listenTCP(8080, dendrite.protocol.ServerFactory())
reactor.callLater(0.5, reactor.connectTCP, "0.0.0.0", 8080, dendrite.protocol.ClientFactory())

reactor.run()