from __future__ import with_statement
import warnings

with warnings.catch_warnings(): 
   warnings.simplefilter("ignore")
   import md5
      # This statement ignores deprecation warning about the
      # md5 module, since Tk and others on OS X depend on it.

import protocol
import tests