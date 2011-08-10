import dendrite
import resource
from twisted.internet import reactor

(soft, hard) = resource.getrlimit(resource.RLIMIT_NOFILE)
resource.setrlimit(resource.RLIMIT_NOFILE, (10000, hard))

reactor.listenTCP(8080, dendrite.protocol.ServerFactory(), backlog=1024)
# reactor.callLater(0.5, reactor.connectTCP, "0.0.0.0", 8080, dendrite.protocol.ClientFactory())

reactor.run()