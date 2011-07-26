from __future__ import with_statement
import warnings

with warnings.catch_warnings(): # ignores deprecation warning about the md5 module.
   warnings.simplefilter("ignore")
   import md5

import protocol
import tests