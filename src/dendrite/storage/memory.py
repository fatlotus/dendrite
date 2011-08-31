from dendrite import Component

class Record(object):
   def __init__(self, database, username, identifier):
      """
      Create a new SQL-like record object.
      
      "Identifier" should be a tuple (type, id)
      explaining the device type and device ID.
      """
      self.identifier = identifier
      self.username = username
      self.database = database
      self.options = { }
      self.enabled = True
   
   def cancel(self):
      """
      Cancels the notification for the specified user. Since there
      may be more operation required than a mere database update, this
      is stubbed out to allow for more complex logic here.
      """
      self.enabled = False

class Database(Component):
   def __init__(self):
      self.people = { }
   
   def set_notifies_in_background(self, username, deviceID, notifies):
      """
      Sets whether the given person is listening for 
      background notification on the specified device.
      
      The deviceID argument should be a tuple (type, ID)
      that contains both the UserAgent and device-specific
      identifier that we want.
      """
      if notifies:
         if username not in self.people:
            self.people[username] = Record(self, username, deviceID)
         
      elif username in self.people:
         if username in self.people:
            self.people[username].cancel()
   
   def is_notifying_in_background(self, username):
      """
      Returns true if the user is registered as having
      requested background notifications.
      """
      return username in self.people
   
   def get_notification_options(self, username):
      """
      Returns the current device-specific options that the end-user
      has specified to send notifications.
      """
      if username in self.people:
         return self.people[username].options.copy()
      else:
         return None
   
   def set_notification_options(self, username, options):
      """
      Sets the current notification configuration that the end-user
      has created.
      """
      if username in self.people:
         self.people[username].options = options.copy()
      