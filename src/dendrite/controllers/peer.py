class Peer(object):
   def __init__(self, reactor, generate_peer_address):
      self.services = [ ]
      self.peers = [ ]
      self.reactor = reactor
      self.generate = generate_peer_address
   
   def connected(self, sender):
      self.peers.append(sender)
   
   def disconnected(self, sender, reason):
      self.peers.remove(sender)
   
   def handle_services(self, sender):
      sender.count(len(self.services))
      
      for service in self.services:
         sender.service(self.services.as_json())