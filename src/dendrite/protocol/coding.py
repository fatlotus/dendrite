import struct
import json

# Serializes a "type-annotated" list of values to a string 
# and returns it.
# 
# Annotated values is a zipped list of tuples (type, value)
# where type is the type "value" should be cast to and "value"
# is the value to be cast.
def encode(types, values):
   if len(types) != len(values):
      raise ValueError("Argument count mismatch: got %i instead of %i" %
         (len(values), len(types)))
   
   fragments = [ ]
   
   for (kind, value) in zip(types, values):
      if type(kind) is type:
         if type(value) is not kind:
            raise TypeError, "value %s must of be of type %s" % (value, kind)
         elif kind in (str, unicode, dict):
            if kind is dict:
               value = json.dumps(value).encode('utf-8')
            if kind is unicode:
               value = value.encode('utf-8')
            fragments.extend(struct.pack('!H', len(value)))
            fragments.append(value)
         elif kind is int:
            fragments.extend(struct.pack('!i', value))
         elif kind is bool:
            fragments.extend(struct.pack('c', 1 if value else 0))
         else:
            raise TypeError, "unsupported type %s" % kind
         
      elif kind == "unsigned" and type(value) in (int, long):
         fragments.append(struct.pack('!I', value))
      else:
         raise TypeError, "invalid type %s (value is %s; a %s)" % (repr(kind), value, type(value))
   
   return ''.join(fragments)

# Decodes some fields given the list of their types.
def decode(message, kinds):
   offset = 0
   values = [ ]
   
   for kind in kinds:
      if kind in (str, unicode, dict):
         length = struct.unpack_from('!H', message, offset)[0]
         offset += struct.calcsize('H')
         read = message[offset:offset+length].decode('utf-8')
         offset += length
         
         if kind is dict:
            read = json.loads(read)
         values.append(read)
      elif kind is int:
         values.extend(struct.unpack_from('!i', message, offset))
         offset += struct.calcsize('i')
      elif kind is bool:
         values.extend(struct.unpack_from('c', message, offset))
         offset += struct.calcsize('c')
      elif kind == "unsigned":
         values.extend(struct.unpack_from('!I', message, offset))
         offset += struct.calcsize('I')
   
   if offset != len(message):
      raise ValueError, "Garbage at the end of fields list."
   
   return values