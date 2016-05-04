# -*- coding: utf-8 -*-
#
# Example WSGI script for use with mod_wgi with Apache
# HTTP Server.

import os
import logging
import beaker.middleware
import s2sproxy.server

# Path to configuration file without .py extension.
CONFIG_PATH = "/etc/s2sproxy/config"

# Logging.
LOGFILE_NAME = '/var/log/s2sproxy/proxy.log'
LOG_LEVEL = logging.DEBUG

logger = logging.getLogger()
hdlr = logging.FileHandler(LOGFILE_NAME)
base_formatter = logging.Formatter( "%(asctime)s %(name)s:%(levelname)s %(message)s")
hdlr.setFormatter(base_formatter)
logger.addHandler(hdlr)
logger.setLevel(LOG_LEVEL)

# Set the working directory. The process will need write
# access to this directory in order for the pysaml2 module
# to write a dbm file it uses internally.
os.chdir('/var/cache/s2sproxy')

# Create the WSGI application. The 'application' method is the WSGI
# application interface.
wsgi_app = s2sproxy.server.WsgiApplication(CONFIG_PATH).application

# Wrap the WSGI application with session middleware. Since most often
# different requests will be processed by different processes use
# file or other state mechanism that will preserve state across
# processes.
SESSION_OPTS = {
    'session.type': 'file',
    'session.data_dir': '/var/cache/s2sproxy',
    'session.lock_dir': '/var/cache/s2sproxy',
    'session.cookie_expires': True,  # Expire cookie used to track the client-side
                                     # of the session at end of browser session.
                                     #
    'session.auto': True             # Session will save itself anytime it is accessed.  
}

application = beaker.middleware.SessionMiddleware(wsgi_app, SESSION_OPTS)
