from dendrite import Component

# How long to wait before a backend is considered
# "dead," in seconds.
EXPIRATION = 60

class Record(object):
   def __init__(self, database, username, identifier):
      # Create a new SQL-like record object.
      # 
      # "Identifier" should be a tuple (type, id)
      # explaining the device type and device ID.
      self.identifier = identifier
      self.username = username
      self.database = database
      self.options = { }
   
   def cancel(self):
      del self.database.people[self.username]

class Database(Component):
   def __init__(self):
      self.people = { }
   
   # Sets whether the given person is listening for 
   # background notification. We don't necessarily claim it:
   # it might be good to have a non-front-facing notification
   # processor.
   def set_notifies_in_background(self, username, deviceID, notifies):
      if notifies:
         self.people[username] = Record(self, username, deviceID)
      elif username in self.people:
         self.people[username].cancel()
   
   # Is this person requesting notifications?
   #
   # Note that "requesting notifications" and "receiving them"
   # are two entirely different states.
   def is_notifying_in_background(self, username):
      return username in self.people
   
   # This method returns the current notifications configuration
   # that the end-user has created.
   #
   def get_notification_options(self, username):
      if username in self.people:
         return self.people[username].options.copy()
      else:
         return None
   
   # Sets the current notification configuration that the end-user
   # has created.
   # 
   def set_notification_options(self, username, options):
      if username in self.people:
         self.people[username].options = options.copy()
      