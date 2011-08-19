from dendrite.protocol import base
from dendrite.controllers import frontend
from dendrite.backends import polling
from dendrite.container import memory as memory_container
from dendrite.storage import memory as memory_storage
from dendrite import ComponentGroup
import resource
from twisted.internet import reactor
import os
import pwd
import grp
import sys
import logging
import signal


def start_server(config={ }):
   url        = config.get("listen", "ssl://0.0.0.0:1337")
   backlog    = config.get("accept_backlog", 1024)
   fd_limit   = config.get("file_descriptor_limit", None)
   user       = config.get("user", None)
   group      = config.get("group", None)
   cert       = config.get("certificate_file", "config/keys/localhost.crt")
   key        = config.get("private_key_file", "config/keys/localhost.key")
   
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
   
   component_group = ComponentGroup()
   
   component_group.add(polling.Backend(), name="api_backend")
   component_group.add(memory_storage.Database(), name="storage_backend")
   component_group.add(memory_container.Container(), name="service_container")
   
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
         group_id = grp.getgrgid(int(group))[2]
      except ValueError:
         try:
            group_id = grp.getgrnam(group)[2]
         except KeyError:
            logging.fatal("Unknown group name %s." % repr(group))
            return 1
      except KeyError:
         logging.fatal("Unknown group ID %s" % repr(group))
         return 1
      
      os.setgrp(group_id)
      logging.info("Running as group ID %i." % os.getegid())
   
   
   if url:
      logging.info("Opening front-facing Dendrite instance on %s..." % url)
      
      controller = frontend.Controller(certificate=cert, private_key=key)
      component_group.add(controller)
      
   component_group.initialize()
   
   if url:
      base.DendriteProtocol.listen(reactor, url, controller, backlog=backlog)
   
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