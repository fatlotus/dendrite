FIELD_TYPES = {
   "echo" : (),
   "fetch" : (str, str),
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
}

INVERTED_TYPE_IDS = dict([v,k] for k,v in TYPE_IDS.items())