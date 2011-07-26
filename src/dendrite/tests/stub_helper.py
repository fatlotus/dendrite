class StubbedMethod(object):
   def __init__(self, wrapping, replace=None):
      if replace:
         wrapping = None
      self.wrapping = wrapping
      self.vargs = None
      self.dargs = None
      self.times_called = 0
   
   def __call__(self, *vargs, **dargs):
      if self.wrapping:
         self.wrapping()
      self.vargs = vargs
      self.dargs = dargs
      self.times_called += 1
   
   def reset(self):
      self.vargs = [ ]
      self.dargs = { }
      self.times_called = 0
   
   def was_called(self):
      return (self.vargs != None)

def stub(obj, name, replace=False):
   setattr(obj, name, StubbedMethod(getattr(obj, name, None), replace))