from Tkinter import *
from tkCommonDialog import Dialog
from twisted.internet import defer, tksupport, reactor

root = Tk()
root.withdraw()

tksupport.install(root)

def better_exit():
   root.destroy()
   reactor.stop()

root.createcommand('exit', better_exit)

class Message(Dialog):
   command = "tk_messageBox"

def authenticate(username, password, info=""):
   d = defer.Deferred()
   
   alert = Message(root, icon='info', type='yesno',
      title="Dendrite: Allow authentication?",
      message="Username: %s\nPassword: %s" % (repr(username), repr(password)),
      detail="Client type: %s\nThese credentials were sent using TLS." % info)
   result = alert.show()
   
   if result == 'yes':
      d.callback(True)
   elif result == 'no':
      d.errback('Invalid username or password')
   
   return d

def listen(method, url, query_string, body, respond):
   window = Toplevel(root, width=200, height=150)
   window.title("Notification Watcher")
   
   Label(window, text="URL:").grid(row=0, column=0, sticky=E)
   Label(window, text="Query string:").grid(row=1, column=0, sticky=E)
   Label(window, text="Body:").grid(row=2, column=0, sticky=E)
   
   mono = ("Monaco", 14)
   
   Label(window, text=repr(url), font=mono).grid(row=0, column=1)
   Label(window, text=repr(query_string), font=mono).grid(row=1, column=1)
   Label(window, text=repr(body), font=mono).grid(row=2, column=1)
   
   def button_clicked(count=[0]):
      count[0] += 1
      respond("updated", { "count" : count[0] })
   
   button = Button(window, text="Trigger Notification", command=button_clicked)
   button.grid(row=3, column=1)
   
   def cancel_request():
      window.destroy()
   
   return cancel_request

def fetch(method, url, query_string, body):
   d = defer.Deferred()
   
   request_length = len(body)
   
   message = """\
Request:
%(method)s %(url)s HTTP/1.1
Connection: close
Content-length: %(request_length)s

%(body)s

(simulated) Response:
HTTP/1.1 200 Okay
Server: the fake one
Content-length: 38

{"DATA": [], "data_type": "task_list"}
""" % locals()
   
   alert = Message(root, icon='info', type='yesno',
      title="Dendrite: HTTP Fetch",
      message=message)
   result = alert.show()
   
   if result == 'yes':
      d.callback({ 'data_type' : 'task_list', 'DATA': [ ] })
   else:
      d.errback("Fetch failed arbitrarily.")
   return d