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
   
   def cancel(self):
      """
      Cancels the notification for the specified user. Since there
      may be more operation required than a mere database update, this
      is stubbed out to allow for more complex logic here.
      """
      del self.database.people[self.username]

class Database(Component):
   def __init__(self):
      self.people = { }
   
   def set_notifies_in_background(self, username, deviceID, notifies):
      """
      Sets whether the given person is listening for 
      background notification. We don't necessarily claim it:
      it might be good to have a non-front-facing notification
      processor.
      """
      if notifies:
         self.people[username] = Record(self, username, deviceID)
      elif username in self.people:
         self.people[username].cancel()
   
   def is_notifying_in_background(self, username):
      """
      Is this person requesting notifications?
      
      Note that "requesting notifications" and "receiving them"
      are two entirely different states.
      """
      return username in self.people
   
   def get_notification_options(self, username):
      """
      This method returns the current notifications configuration
      that the end-user has created.
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
      