from dendrite import Component

# How long to wait before a backend is considered
# "dead," in seconds.
EXPIRATION = 60

class Record(object):
   def __init__(self, database, username, identifier):
      # Create a new SQL-like record object.
      # 
      # "Identifier" should be a tuple (kind, data)
      # explaining the device type and device ID.
      self.identifier = identifier
      self.username = username
      self.database = database
      self.options = { }
      self.last_updated = 0
   
   def refresh(self):
      # Consider this node "updated." The backend
      # should periodically call this method to
      # indicate active status.
      self.last_updated = time.time()
   
   def is_expired(self):
      # Consider this node dead if the backend has stopped 
      # responding or is having clock issues.
      
      return (
         (self.last_updated < (time.time() - EXPIRATION)) or 
         (self.last_updated > (time.time() + 30))
      )
   
   def expire(self):
      # <OPEN TRANSACTION>
      self.last_updated = 0
      # <CLOSE TRANSACTION>
   
   def is_cancelled(self):
      return (self.username in self.database.people)
   
   def cancel(self):
      # <OPEN TRANSACTION>
      del self.database.people[self.username]
      # <CLOSE TRANSACTION>


class Database(Component):
   def __init__(self):
      self.people = { }
   
   # Retrieves "count" devices from the queue.
   def retrieve_devices(self, count=100):
      results = [ ]
      
      # <OPEN TRANSACTION>
      for record in self.people.values():
         if record.is_expired():
            record.refresh()
            results.append(record)
            
            if len(results) >= count:
               break
      # <CLOSE TRANSACTION>
      
      return results
   
   # Sets whether the given person is listening for 
   # background notification. We don't necessarily claim it:
   # it might be good to have a non-front-facing notification
   # processor.
   def set_notifies_in_background(self, username, deviceID, notifies):
      if notifies:
         # <OPEN TRANSACTION>
         self.people[username] = Record(self, username, deviceID)
         # <CLOSE TRANSACTION>
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
      