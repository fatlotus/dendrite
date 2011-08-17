FIELD_TYPES = {
   "echo" : (),
   "fetch" : (str, str, str, str),
   "data" : (dict,),
   "starttls" : (),
   "success" : (),
   "failure" : (str,str),
   "login" : (str, str),
   "identify" : (),
   "identity" : (str, str),
   "listen" : (str, str),
   "cancel" : (),
   "notify" : (str, dict),
   "session" : (),
   "up" : ('unsigned',),
   "down" : ('unsigned',),
   "node" : (str, 'unsigned'),
   "services" : (),
   "service" : (dict),
   "count" : ('unsigned',)
}

TYPE_IDS = {
   "echo" : 0x1,
   "fetch" : 0x2,
   "data" : 0x8,
   "success" : 0xA,
   "failure" : 0xB,
   "login" : 0x9,
   "identify" : 0xD,
   "identity" : 0xC,
   "listen" : 0x3,
   "cancel" : 0x5,
   "notify" : 0x4,
   "session" : 0x6,
   "up" : 0xE,
   "down" : 0xF,
   "node" : 0x10,
   "services" : 0x11,
   "service" : 0x12,
   "count" : 0x13 
}

INVERTED_TYPE_IDS = dict([v,k] for k,v in TYPE_IDS.items())