import sys
import json
from dendrite import Component

if 'nose' not in sys.modules:
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

class Resource(object):
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
      
      Button(window,
       text="Send response",
       command=trigger_update).grid(row=5, column=1)
   
   def fetch(self, success, failure):
      self._make_ui(True, success, failure)
   
   def listen(self, update, failure):
      self._make_ui(False, update, failure)

class Backend(Component):
   def authenticate(self, username, password):
      d = defer.Deferred()

      alert = Message(root, icon='info', type='yesno',
         title="Dendrite: Allow authentication?",
         message="Username: %s\nPassword: %s" % (repr(username), repr(password)),
         detail="Some tests require that you enter valid credentials.")
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
   
   def resource(self, *args):
      return Resource(*args)
