import struct
import json

# Serializes a "type-annotated" list of values to a string 
# and returns it.
# 
# Annotated values is a zipped list of tuples (type, value)
# where type is the type "value" should be cast to and "value"
# is the value to be cast.
def encode(annotated_values):
	fragments = [ ]
	
	for (kind, value) in annotated_values:
		if type(kind) is type:
			if type(value) is not kind:
				raise TypeError, "value %s must of be of type %s" % (value, kind)
			elif kind in (str, unicode):
				if kind is unicode:
					value = value.encode('utf-8')
				fragments.append(struct.pack('!Hs', len(value), value))
			elif kind is int:
				fragments.append(struct.pack('!i', value))
			elif kind is dict:
				fragments.append(struct.pack('!Hs', 2, "{}"))
			elif kind is bool:
				fragments.append(struct.pack('c', 1 if value else 0))
			
		elif kind == "unsigned" and type(value) is int:
			fragments.append(struct.pack('!I', value))
 		else:
			raise TypeError, "invalid type %s" % repr(kind)
	
	return ''.join(fragments)

# Decodes some fields given the list of their types.
def decode(string, kinds):
	offset = 0
	values = [ ]
	
	for kind in kinds:
		if kind in (str, unicode, dict):
			length = struct.unpack_from('!H', message, offset)
			offset += struct.calcsize('H')
			read = kind[offset:offset+length].decode('utf-8')
			offset += length
			
			if kind is dict:
				read = json.loads(read)
			values.append(read)
		elif kind is int:
			values = struct.unpack_from('!i', message)
			offset += struct.calcsize('i')
		elif kind is bool:
			values = struct.unpack_from('c', message)
			offset += struct.calcsize('c')
		elif kind == "unsigned":
			values = struct.unpack_from('!I', message)
			offset += struct.calcsize('I')
	
	if offset != len(string) - 1:
		raise ValueError, "Garbage at the end of fields list."
	
	return values