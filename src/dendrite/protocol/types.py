FIELD_TYPES = {
   "echo" : (),
   "fetch" : (str, str),
   "data" : (dict,),
   "starttls" : (),
   "success" : (),
   "failed" : (str,),
}

TYPE_IDS = {
   "echo" : 0x1,
   "fetch" : 0x2,
   "data" : 0x8,
   "starttls" : 0x5,
   "success" : 0xA,
   "failed" : 0xB,
}

INVERTED_TYPE_IDS = dict([v,k] for k,v in TYPE_IDS.items())