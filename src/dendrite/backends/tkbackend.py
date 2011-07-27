from Tkinter import *
from tkCommonDialog import Dialog
from twisted.internet import defer, tksupport, reactor

root = Tk()
root.withdraw()

tksupport.install(root)

class Message(Dialog):
   command = "tk_messageBox"

def authenticate(username, password, info=""):
   d = defer.Deferred()
   
   alert = Message(root, icon='info', type='yesno',
      title="Dendrite: Allow authentication?",
      message="Username: %s\nPassword: %s" % (repr(username), repr(password)),
      detail="Client type: %s\nThese credentials were sent using TLS." % info)
   result = alert.show()
   
   print repr(result)
   
   if result == 'yes':
      d.callback(True)
   elif result == 'no':
      d.errback('Invalid username or password')
   
   return d

def fetch(method, url, query_string, body):
   d = defer.Deferred()
   
   # real HTTP request happens here.
   
   request_length = len(body)
   
   message = """\
Request:
%(method)s %(url)s HTTP/1.1
Connection: close
Content-length: %(request_length)s

%(body)s

Response:
HTTP/1.1 200 Okay
Server: the fake one
Content-length: 0""" % locals()
   
   alert = Message(root, icon='info', type='yesno',
      title="Dendrite: HTTP Fetch",
      message=message)
   result = alert.show()
   
   if result == 'yes':
      d.callback({ 'data_type' : 'task_list', 'DATA': [ ] })
   else:
      d.errback("Fetch failed arbitrarily.")
   return d