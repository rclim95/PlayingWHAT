"""Initializes the `playwhat.service` module"""

import logging
import os

# The main logger for this module
LOGGER = logging.getLogger(__package__)

# The path to where the PID file should be stored
PATH_PID = os.path.join(os.sep, "run", "playwhat", "playwhat.pid")

# The path to where the Unix socket should be stored
PATH_UNIX_SOCKET = os.path.join(os.sep, "run", "playwhat", "playwhat.sock")
