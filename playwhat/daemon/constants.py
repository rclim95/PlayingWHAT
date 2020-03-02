"""Define constants needed by `playwhat.daemon`"""

import os

# The path to where the PID file should be stored
PATH_PID = os.path.join(os.sep, "run", "playwhat", "playwhat.pid")

# The path to where the Unix socket should be stored
PATH_UNIX_SOCKET = os.path.join(os.sep, "run", "playwhat", "playwhat.sock")
