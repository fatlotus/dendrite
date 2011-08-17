from dendrite import diff
from nose.tools import *

def apply_differences(original, differences):
   for (change, data) in differences:
      index = data.get("index", None)
      
      if change == "refresh":
         fail("Refresh opcode blocked while testing.")
         original = data['DATA'][:]
      else:
         if change == "insert":
            original.insert(data["index"], data["data"])
         elif change == "replace":
            original[index] = data["data"]
         elif change == "remove":
            original.pop(index)
   
   return original

@nottest
def differencing_subtest(a, b):
   # Pad a and b to ensure continuity.
   a = [ { 'href' : '1' } ] + a + [ { 'href' : '2' }]
   b = [ { 'href' : '1' } ] + b + [ { 'href' : '2' }]
   
   # Package the list as an list-style record.
   a_wrapper = { 'DATA_TYPE' : 'stuff_list', 'DATA' : a }
   b_wrapper = { 'DATA_TYPE' : 'stuff_list', 'DATA' : b }
   
   differences = diff.diff(a_wrapper, b_wrapper)
   
   result = apply_differences(a[:], differences)
   
   eq_(b, result)

def test_empty_difference():
   differencing_subtest ([], [])

def test_insertion():
   differencing_subtest ([ ], [ { 'href' : 'c' } ])

def test_deletion():
   differencing_subtest ([ { 'href' : 'a' } ], [ ])

def test_update():
   differencing_subtest (
      [ { 'href' : 'a', 'value' : 'q' } ],
      [ { 'href' : 'a', 'value' : 'q' }]
   )
   
# This test basically just fuzzes the differencing library until
# a whole bunch of bugs fall out.
def test_composite():
   for r in xrange(0, 20, 3):
      start = [ ]
      end = [ ]
      
      for i in xrange(r):
         if i % 3 != 0:
            start.append({ 'href' : 'A%i' % i })
         
         if i % 2 == 0:
            end.append({ 'href' : 'A%i' % i })
   
      differencing_subtest(start, end)