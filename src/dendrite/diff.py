import difflib

# Extract an identifier for an entity.
def _id_of(item):
   if "id" in item:
      return item["id"]
   elif "href" in item:
      return item["href"]
   elif "task_id" in item:
      return item["task_id"]
   elif "canonical_name" in item:
      return item["canonical_name"]

# This is probably the ugliest code in the entire project.
def diff(a, b):
   """
   Calculates a list of tuples (type, data) of the changes between the old and
   new states "a" and "b," respectively.
    
   If there are none, simply return an empty list.
   """
   
   changes = [ ]
   
   # Optimize trivial cases.
   if a == b:
      return [ ]
      
   try:
      # Verify that the data type hasn't changed.
      #
      # If it has, then we'll treat it as a failure and refresh it.
      if a["DATA_TYPE"] != b["DATA_TYPE"]:
         raise ValueError
      
      # Same for non-list types.
      if not a["DATA_TYPE"].endswith("_list"):
         raise ValueError
      
      # Extract a list of identifiers to track the changes to the data.
      a_ids = [ _id_of(x) for x in a["DATA"] ]
      b_ids = [ _id_of(x) for x in b["DATA"] ]
      
      # Trigger the difflib sequencing algorithm.
      matcher = difflib.SequenceMatcher()
      matcher.set_seqs(a_ids, b_ids)
      
      # Iterate through all changes.
      # 
      # This has that extra [::-1] because we need to calculate changes
      # in reverse order: anything else would require adjustment of IDs.
      for (opcode, sa, ea, sb, eb) in matcher.get_opcodes()[::-1]:
         if opcode == "equal":
            
            # Iterate through all equal identifiers and check for changing
            # value properties.
            for offset in xrange(0, ea - sa):
               
               # If the record has changed, then send an 'update'
               # notification.
               if a["DATA"][sa + offset] != b["DATA"][sb + offset]:
                  
                  # This update uses the initial indices but the resulting
                  # data.
                  changes.append(('update', {
                     'index' : sa + offset,
                     'data' : b["DATA"][sb + offset]
                  }))
                  
         elif opcode == "replace":
            # Treat replacement as insertion and deletion:
            #
            # We're assuming that identity changes are basically just
            # new data.
            
            # Iterate through all things not in the final value.
            for offset in xrange(0, ea - sa):
               
               # Don't add + offst because we're removing as-we-go.
               changes.append(('remove', {
                  'index' : sa
               }))
            
            # Iterate through all items inserted relative to the
            # initial list.
            for offset in xrange(0, eb - sb):
               
               # Insert it in the correct order (+offst) using the
               # final data.
               changes.append(('insert', {
                  'index' : sa + offset,
                  'data' : b["DATA"][sb + offset]
               }))
            
         elif opcode == "insert":
            
            # Treat insertions as above: use the final length but
            # the initial offsets and final data.
            for offset in xrange(0, eb - sb):
               changes.append(('insert', {
                  'index' : sa,
                  'data': b["DATA"][sb + offset]
               }))
         
         elif opcode == "delete":
            
            # Treat deletions as with replace: use the initial
            # indices and delete incrementally.
            for offset in xrange(0, ea - sa):
               
               # Don't add + offst because we're removing as-we-go.
               changes.append(('remove', {
                  'index' : sa
               }))
         
         else:
            
            # General safety block: ensure that in the event of 
            # a failure, we can treat it as a complete rewrite.
            raise ValueError("unhandled option: %s" % opcode)
   
   # Handle all errors as as refreshes.
   except (ValueError, IndexError):
      changes = [ ("refresh", b) ]
   
   return changes