import dendrite
import resource
from twisted.internet import reactor
import os
import pwd
import grp
import sys
import logging
import signal

def start_server(config={ }):
   port       = config.get("listen_port", None)
   backlog    = config.get("accept_backlog", 1024)
   fd_limit   = config.get("file_descriptor_limit", None)
   user       = config.get("user", None)
   group      = config.get("group", None)
   
   if sys.stdout.isatty():
      logging.basicConfig(
         datefmt="%m-%d %H:%M:%S %Z",
         format="%(asctime)s %(levelname)10s | %(message)s",
         level=logging.INFO)
   else:
      logging.basicConfig(
         datefmt="%m-%d %H:%M:%S %Z",
         format="%(asctime)s %(levelname)10s | %(message)s",
         filename="log/errors.log", level=logging.INFO)
   
   header = """\
+------------------------+
|                 ____@  |
|  ()()-----\____/       |
| ()()    |      \_____@ |
|         \___/--\       |
|                 \--@   |
+------------------------+
|  Dendrite Initialized  |
+------------------------+\
""".split('\n')
   
   for line in header:
      logging.info(line)
   
   if fd_limit is not None:
      try:
         (soft, hard) = resource.getrlimit(resource.RLIMIT_NOFILE)
         resource.setrlimit(resource.RLIMIT_NOFILE, (fd_limit, hard))
      except ValueError, e:
         logging.error(
          "Could not set file descriptor limit to %i: %s" %
          (fd_limit, repr(e))
         )
         return 1
   
   if port:
      logging.info("Opening Dendrite on :%s..." % port)
   
      reactor.listenTCP(port, dendrite.protocol.ServerFactory(config),
         backlog=backlog)
   
   if os.geteuid() is 0:
      logging.warn("The Dendrite server is not tested to run EUID root.")
      if user is None:
         logging.fatal(
          "You must specify the user attribute if you wish to start "
          "Dendrite as root."
         )
         return 1 
   
   if user is not None:
      try:
         user_id = pwd.getpwuid(int(user))[2]
      except ValueError:
         try:
            user_id = pwd.getpwnam(user)[2]
         except KeyError:
            logging.fatal("Unknown user name %s" % repr(user))
            return 1
      except KeyError:
         logging.fatal("Unknown user ID %s" % repr(user))
         return 1
      
      os.setuid(user_id)
      
      logging.info("Running as user ID %i." % os.geteuid())
   
   if group is not None:
      try:
         group_id = grp.getgrgid(int(user))[2]
      except ValueError:
         try:
            group_id = grp.getgrnam(user)[2]
         except KeyError:
            logging.fatal("Unknown group name %s." % repr(group))
            return 1
      except KeyError:
         logging.fatal("Unknown group ID %s" % repr(group))
         return 1
      
      os.setgrp(group_id)
      logging.info("Running as group ID %i." % os.getegid())
   
   logging.info("Dendrite started.")
   
   def stop_via_signal(*vargs):
      if sys.stdout.isatty():
         sys.stdout.write("\r")
         sys.stdout.flush()
      logging.info("Received SIGINT-")
      stop_server()
   
   signal.signal(signal.SIGINT, stop_via_signal)
   
   reactor.run()

def stop_server():
   logging.info("Dendrite terminating...")
   
   reactor.stop()
   
   logging.info("Dendrite terminated.")