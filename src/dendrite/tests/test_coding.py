from dendrite.protocol import coding
from nose.tools import *

TYPES = (int, str, unicode, dict, 'unsigned', bool)

@nottest
def initialize_type(kind):
   if kind is unicode:
      return u'\u03c0\u00e9\u00f1\u00bf'
   elif kind is dict:
      return { 'str': 'val', 'ary' : [ { '1' : 2, 'bool' : True } ] }
   elif kind == 'unsigned':
      return 1 << 32l - 1
   elif kind == int:
      return -1
   elif kind == bool:
      return True
   else:
      return kind()

@nottest
def verify(*kinds):
   values = [ initialize_type(kind) for kind in kinds ]
   results = list(coding.decode(coding.encode(kinds, values), kinds))
   
   eq_(results, values, "before and after encoding not equal.")

def test_composite_types():
   verify()
   
   for a in TYPES:
      verify(a)
   
   for a in TYPES:
      for b in TYPES:
         verify(a, b)
   
   for a in TYPES:
      for b in TYPES:
         for c in TYPES:
            verify(a, b, c)

@raises(ValueError)
def test_invalid_boolean():
   coding.decode("A", [ bool ])

@raises(ValueError)
def test_max_unsigned():
   coding.encode([ 'unsigned' ], [ 2**32 ])

@raises(ValueError)
def test_min_unsigned():
   coding.encode([ 'unsigned' ], [ -1 ])

@raises(ValueError)
def test_max_int():
   coding.encode([ int ], [ 2**31 ])

@raises(ValueError)
def test_min_int():
   coding.encode([ int ], [ -2**31 ])