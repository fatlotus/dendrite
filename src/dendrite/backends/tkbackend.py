from Tkinter import *
from tkCommonDialog import Dialog
from twisted.internet import defer, tksupport, reactor
import json

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
      d.callback({
         "fullname" : "TkBackend Test User",
         "username" : username,
         "email" : "user@email.tld",
         "status" : ""
      })
   elif result == 'no':
      d.errback('Invalid username or password')
   
   return d

class Request(object):
   def __init__(self, session, method, url, query_string, body):
      self.method = method
      self.url = url
      self.query_string = query_string
      self.body = body
   
   def cancel(self):
      if self._window:
         self._window.destroy()
   
   def _make_ui(self, is_fetch, update, failure):
      mono = ("Monaco", 14)
      
      verb = ("Calling" if is_fetch else "Listening to")
      
      window = Toplevel(root, width=200, height=150)
      window.title("%s %s %s" % (verb, self.method, self.url))
      
      self._window = window
      
      Label(window, text="Method:").grid(row=0, column=0, sticky=E)
      Label(window, text="URL:").grid(row=1, column=0, sticky=E)
      Label(window, text="Query string:").grid(row=2, column=0, sticky=E)
      Label(window, text="Request Body:").grid(row=3, column=0, sticky=E)
      Label(window, text="Response Body:").grid(row=4, column=0, sticky=E)
      
      Label(window, text=repr(self.method), font=mono).grid(row=0, column=1)
      Label(window, text=repr(self.url), font=mono).grid(row=1, column=1)
      Label(window, text=repr(self.query_string), font=mono).grid(row=2, column=1)
      Label(window, text=repr(self.body), font=mono).grid(row=3, column=1)
      
      text = Text(window, width=40, height=5)
      text.grid(row=4, column=1, padx=5, pady=5)
      text.insert(1.0, "{\"DATA\":[],\"data_type\":\"transfer_list\"}")
      
      def trigger_update():
         try:
            data = json.loads(text.get('1.0', 'end'))
         except Exception, e:
            Message(window, icon='error',
               message=str(e),
               detail="Please correct the error and try again."
            ).show()
         else:
            if is_fetch:
               update(data)
               window.destroy()
            else:
               update("refresh", data)
      
      Button(window, text="Send response", command=trigger_update).grid(row=5, column=1)
   
   def fetch(self, success, failure):
      self._make_ui(True, success, failure)
   
   def listen(self, update, failure):
      self._make_ui(False, update, failure)

def listen(method, url, query_string, body, respond):
   window = Toplevel(root, width=200, height=150)
   window.title("Notification Watcher")
   
   Label(window, text="URL:").grid(row=0, column=0, sticky=E)
   Label(window, text="Query string:").grid(row=1, column=0, sticky=E)
   Label(window, text="Request Body:").grid(row=2, column=0, sticky=E)
   
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