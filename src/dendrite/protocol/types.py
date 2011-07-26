FIELD_TYPES = {
   "echo" : (),
   "fetch" : (str, str),
   "data" : (dict,),
}

TYPE_IDS = {
   "echo" : 0x1,
   "fetch" : 0x2,
   "data" : 0x8,
}

INVERTED_TYPE_IDS = dict([v,k] for k,v in TYPE_IDS.items())