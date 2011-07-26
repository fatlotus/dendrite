from __future__ import with_statement
import warnings

with warnings.catch_warnings():
   warnings.simplefilter("ignore")
   from twisted.internet import _sslverify

import dendrite
from twisted.internet import reactor

reactor.listenTCP(8080, dendrite.protocol.ServerFactory())
reactor.callLater(0.5, reactor.connectTCP, "0.0.0.0", 8080, dendrite.protocol.ClientFactory())

reactor.run()