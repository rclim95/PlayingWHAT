"""The main file that is executed for the `playwhat.service` package"""

import asyncio
import logging
import os
import signal
import sys
import daemon
import dotenv
from daemon.pidfile import PIDLockFile
import playwhat
from playwhat.service import LOGGER, server
from playwhat.service.constants import PATH_PID

def on_sigterm(signum, frame): # pylint: disable=unused-argument
    """Handles `SIGTERM` from the service"""
    server.stop()

def on_sighup(signum, frame): # pylint: disable=unused-argument
    """
    Handles the `SIGHUP` from the service, which indicates the user wants to reload the service's 
    configuration
    """
    # Determine if there's an environment variable called ENV_FILE. If so, we'll load the
    # .env file specified in the ENV_FILE path
    env_file_path = os.getenv("ENV_FILE", None)
    if os.path.exists(env_file_path):
        LOGGER.info("Reloading .env file from %s", env_file_path)
        dotenv.load_dotenv(env_file_path)
    else:
        LOGGER.info("Reloading .env file from default location")
        dotenv.load_dotenv()

    # Show some useful information about the environment variables we've loaded
    LOGGER.debug("SPOTIFY_CLIENT_ID = %s", os.getenv(playwhat.ENV_CLIENT_ID))
    LOGGER.debug("SPOTIFY_CLIENT_SECRET = %s", "*" * len(os.getenv(playwhat.ENV_CLIENT_SECRET)))
    LOGGER.debug("SPOTIFY_USER_TOKEN = %s", "*" * len(os.getenv(playwhat.ENV_USER_TOKEN)))

    # Success!
    LOGGER.info("Reloaded .env successfully")

def main():
    """The main entry point"""
    # Set up basic logging that prints out to the STDOUT.
    logging.basicConfig(level=logging.DEBUG,
                        format="[%(levelname)s] %(asctime)s - %(name)s: %(message)s",
                        stream=sys.stdout)

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

    try:
        LOGGER.info("Starting PlayingWHAT Service...")

        # Determine if there's an environment variable called ENV_FILE. If so, we'll load the
        # .env file specified in the ENV_FILE path
        env_file_path = os.getenv("ENV_FILE", None)
        if os.path.exists(env_file_path):
            LOGGER.info("Loading .env file from %s", env_file_path)
            dotenv.load_dotenv(env_file_path)
        else:
            LOGGER.info("Loading .env file from default location")
            dotenv.load_dotenv()

        # Show some useful information about the environment variables we've loaded
        LOGGER.debug("SPOTIFY_CLIENT_ID = %s", os.getenv(playwhat.ENV_CLIENT_ID))
        LOGGER.debug("SPOTIFY_CLIENT_SECRET = %s", "*" * len(os.getenv(playwhat.ENV_CLIENT_SECRET)))
        LOGGER.debug("SPOTIFY_USER_TOKEN = %s", "*" * len(os.getenv(playwhat.ENV_USER_TOKEN)))

        with context:
            asyncio.run(server.start())
    except Exception:
        LOGGER.exception("Failed to start PlayingWHAT Service")


if __name__ == "__main__":
    main()
