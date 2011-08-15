import difflib

def _id_of(item):
   if "id" in item:
      return item["id"]
   elif "href" in item:
      return item["href"]
   elif "task_id" in item:
      return item["task_id"]
   elif "canonical_name" in item:
      return item["canonical_name"]

def diff(a, b):
   """
   Calculates a list of tuples (type, data) of the changes between the old and
   new states "a" and "b," respectively.
    
   If there are none, simply return an empty list.
   """
   
   changes = [ ]
   
   if a == b:
      return [ ]
      
   try:
      if a["DATA_TYPE"] != b["DATA_TYPE"]:
         raise ValueError
      
      if not a["DATA_TYPE"].endswith("_list"):
         raise ValueError
      
      a_ids = [ _id_of(x) for x in a["DATA"] ]
      b_ids = [ _id_of(x) for x in b["DATA"] ]
      
      matcher = difflib.SequenceMatcher()
      matcher.set_seqs(a_ids, b_ids)
      
      print repr(matcher.get_opcodes())
      
      for (opcode, sa, ea, sb, eb) in matcher.get_opcodes():
         if opcode == "equal":
            for offset in xrange(0, ea - sa):
               if a["DATA"][sa + offset] != b["DATA"][sb + offset]:
                  changes.append(('update', {
                     'index' : sa + offset,
                     'data' : b["DATA"][sb + offset]
                  }))
                  
         elif opcode == "replace":
            for offst in xrange(0, eb - sb):
               changes.append(('remove', {
                  'index' : sa + offst
               }))
               changes.append(('insert', {
                  'index' : sa + offst,
                  'data' : b["DATA"][sb + offst]
               }))
         elif opcode == "insert":
            for offst in xrange(0, eb - sb):
               changes.append(('insert', {
                  'index' : sa,
                  'data': b["DATA"][sb + offst]
               }))
         else:
            raise ValueError("unhandled option: %s" % opcode)
         
   except (ValueError, IndexError):
      changes = [ ("refresh", b) ]
   
   return changes