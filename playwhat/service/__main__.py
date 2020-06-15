"""The main file that is executed for the `playwhat.service` package"""

import asyncio
import os
import signal
import sys
import daemon
from daemon.pidfile import PIDLockFile
import playwhat
from playwhat.service import LOGGER, PATH_PID, service

def on_sigterm(signum, frame): # pylint: disable=unused-argument
    """Handles `SIGTERM` from the service"""
    service.stop()

def on_sighup(signum, frame): # pylint: disable=unused-argument
    """
    Handles the `SIGHUP` from the service, which indicates the user wants to reload the service's
    configuration
    """
    service.reload()

def main():
    """The main entry point"""
    playwhat.setup_logging(logger=LOGGER)
    playwhat.setup_environment_vars(logger=LOGGER)

    # Show some useful information about the environment variables we've loaded
    LOGGER.debug("SPOTIFY_CLIENT_ID = %s", os.getenv(playwhat.ENV_CLIENT_ID))
    LOGGER.debug("SPOTIFY_CLIENT_SECRET = %s", "*" * len(os.getenv(playwhat.ENV_CLIENT_SECRET)))
    LOGGER.debug("SPOTIFY_USERNAME = %s", os.getenv(playwhat.ENV_USERNAME))

    try:
        # Setup the daemon context
        context = daemon.DaemonContext(
            detach_process=True,
            pidfile=PIDLockFile(PATH_PID),
            working_directory=os.getcwd(),
            signal_map={
                signal.SIGTERM: on_sigterm,
                signal.SIGHUP: on_sighup
            },
            stdout=sys.stdout,
            stderr=sys.stderr
        )

        with context:
            LOGGER.info("Starting daemon context...")
            asyncio.run(service.start())
    except Exception: # pylint: disable=broad-except
        LOGGER.exception("Failed to start PlayingWHAT Service")

if __name__ == "__main__":
    main()
