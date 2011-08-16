from dendrite.protocol import coding
import unittest

TYPES = (int, str, unicode, dict, 'unsigned', bool)

class TestEncoding(unittest.TestCase):
   def initialize_type(self, kind):
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
   
   def verify(self, *kinds):
      values = [ self.initialize_type(kind) for kind in kinds ]
      results = list(coding.decode(coding.encode(kinds, values), kinds))
      
      self.assertEqual(results, values, "before and after encoding not equal.")
   
   def test_composite_types(self):
      self.verify()
      
      for a in TYPES:
         self.verify(a)
      
      for a in TYPES:
         for b in TYPES:
            self.verify(a, b)
      
      for a in TYPES:
         for b in TYPES:
            for c in TYPES:
               self.verify(a, b, c)
   
   def test_invalid_boolean(self):
      self.assertRaises(ValueError, lambda: coding.decode("A", [ bool ]))
   
   def test_range_integers(self):
      self.assertRaises(ValueError, lambda: coding.encode([ 'unsigned' ], [ 2**32 ]))
      self.assertRaises(ValueError, lambda: coding.encode([ int ], [ 2**31 ]))
      self.assertRaises(ValueError, lambda: coding.encode([ 'unsigned' ], [ -1 ]))
      self.assertRaises(ValueError, lambda: coding.encode([ int ], [ -2**31 ]))