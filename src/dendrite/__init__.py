from __future__ import with_statement
import warnings

with warnings.catch_warnings():
   warnings.simplefilter("ignore")
   from twisted.internet import _sslverify

import protocol
import tests