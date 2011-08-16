# Generic python coding/decoding module. It is compliant with the
# java.io.Data- processors, except for the small detail that strings
# have been extended to support up to 2**32 bytes of data, rather than
# merely 2**16.
# 
# Data types:
# 
#  str         A UTF-8 string, prefixed with a 32-bit length specifier.
#  dict        A dictionary encoded as JSON and then as a string, above.
#  'unsigned'  A 32-bit unsigned integer.
#  int         A 32-bit signed integer.
#  bool        An 8-bit boolean value. This must either be a constant (1)
#               or a constant (0). Anything else is an error.
# 
# The BOM on the str is optional but accepted, again for Java
# compatability.

import struct
import json

# Serializes a "type-annotated" list of values to a string 
# and returns it.
# 
# Annotated values is a zipped list of tuples (type, value)
# where type is the type "value" should be cast to and "value"
# is the value to be cast.
def encode(types, values):
   
   # Validate inputs for sanity, because zip does not.
   if len(types) != len(values):
      raise ValueError("Argument count mismatch: got %i instead of %i" %
         (len(values), len(types)))
   
   fragments = [ ]
   
   try:
      for (kind, value) in zip(types, values):
         
         # This is some very seriously hardened code, so every edge
         # case must always be checked for and tested.
         if kind == int and type(value) in (int, long):
            
            # Check overflow. Even if the protocol can still transfer
            # a (truncated) version, we'd rather ensure strict
            # compatability. 
            if value >= 2**31 or value <= -2**31:
               raise ValueError('Invalid int: values are limited '
                 'to 32 bits, signed.')
            
            # The default int type is signed, so simply write it
            # out to the stream, packed correctly, of course.
            fragments.extend(struct.pack('!i', value))
            
         elif kind == "unsigned" and type(value) in (int, long):
            
            # Again, check for overflow. I may be conservative
            # in my edge cases, but they're edge cases for a reason.
            if value < 0 or value >= 2**32:
               raise ValueError('Invalid unsigned: values are limited '
                 'to 32-bits, unsigned.')
            
            # Write the value out.
            fragments.append(struct.pack('!I', value))
               
         elif type(kind) is type:
            
            # Dendrite is a statically-typed protocol, so we enable
            # static-typing here to ensure type compliance.
            # 
            # This TypeError exception is the only failure case that
            # does not return a ValueError since it should occur
            # only as a result of programmer error.
            # 
            if type(value) is not kind:
               raise TypeError, "value %s must of be of type %s" % (value, kind)
               
            elif kind in (str, unicode, dict):
               # Encode structured data first.
               if kind is dict:
                  value = json.dumps(value)
               
               # Next, encode advanced character sets
               # and encode as a byte buffer.
               if kind is unicode:
                  value = value.encode('utf-8')
               
               if len(value) > 2**32:
                  raise ValueError('Invalid string: length specifiers '
                    'are bounded at 32 bits.')
               
               # Prepend the length specifier and write the data out.
               fragments.extend(struct.pack('!I', len(value)))
               fragments.append(value)
               
            elif kind is bool:
               
               # Encoding a boolean is much simpler: no edge cases!
               # We simply treat it as a C 'char' (defined to be one
               # byte), and shove it on the stream.
               fragments.extend(struct.pack('!B', 1 if value else 0))
            else:
               
               # Again, consider all programmer typing errors as 
               # "unhandleable," and do not specify that the caller
               # define them.
               raise TypeError, "unsupported type %s" % kind
         
         else:
            
            # Again, raise for an invalid type.
            raise TypeError("Invalid type %s (value is %s; a %s)" %
              (repr(kind), value, type(value)))
   
   # Mask all struct.error exceptions as ValueErrors so that
   # the caller does not need to know about the struct module.
   except struct.error, e:
      raise ValueError(e)
   
   # Apparently this is the fastest way of creating buffers
   # in Python.
   return ''.join(fragments)

# Decodes the fields from the given message given a list 
# of python types do decode from.
def decode(message, kinds):
   # Offsetting and slicing is, I think, one of the faster
   # ways to access a buffer in Python.
   offset = 0
   values = [ ]
   
   try:
      for kind in kinds:
         if kind in (str, unicode, dict):
            # Unpack the length header and mark it in the offset.
            length = struct.unpack_from('!I', message, offset)[0]
            offset += struct.calcsize('!I')
            
            # The read message should be a unicode string, so decode
            # it as UTF-8.
            read = message[offset:offset+length].decode('utf-8')
            offset += length
            
            # If we're expecting structured data, then parse it. If
            # this is invalid JSON, then the json library will throw a 
            # ValueError exception, just as with marshal and pickle.
            if kind is dict:
               read = json.loads(read)
            
            # Append to the resulting variable.
            values.append(read)
         
         elif kind is int:
            # Integers are pretty easy: we just unpack and bump the
            # offset variable.
            values.extend(struct.unpack_from('!i', message, offset))
            offset += struct.calcsize('i')
            
         elif kind is bool:
            # Parse the boolean as a single byte and increase the
            # offset.
            byte_value = struct.unpack_from('!B', message, offset)[0]
            offset += struct.calcsize('!B')
            
            # Check the value of this boolean rigorously. Anything 
            # else might signal protocol desynchronicity.
            if byte_value == 0:
               bool_value = False
            elif byte_value == 1:
               bool_value = True
            else:
               raise ValueError, 'Invalid boolean value: %s' % repr(byte_value)
            
            # Record the value parsed.
            values.append(bool_value)
         
         elif kind == "unsigned":
            # Unsigned is pretty much just like signed, above, since
            # struct does all of our work for us.
            values.extend(struct.unpack_from('!I', message, offset))
            offset += struct.calcsize('I')
   
   # Treat any struct parsing errors or unicode parsing errors
   # as ValueErrors and propagate to the caller.
   except (struct.error, UnicodeDecodeError), e:
      raise ValueError(e)
   
   # Final assertions to ensure protocol synchronicity.
   if offset != len(message):
      raise ValueError, "Garbage at the end of fields list."
   
   return values