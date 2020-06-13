"""The main file that is executed for the `playwhat.service` package"""

import asyncio
import logging
import os
import signal
import sys
import daemon
import dotenv
from daemon.pidfile import PIDLockFile
from playwhat.service import LOGGER, server, client
from playwhat.service.constants import PATH_PID
from playwhat.painter.types import DeviceType, RepeatStatus, PainterOptions

def on_sigterm(signum, frame):
    """Handles `SIGTERM` from the service"""
    server.stop()

def main():
    """The main entry point"""
    # Set up basic logging that prints out to the STDOUT.
    logging.basicConfig(level=logging.DEBUG,
                        format="[%(levelname)s] %(asctime)s - %(name)s: %(message)s",
                        stream=sys.stdout)

    logger = logging.getLogger()
    context = daemon.DaemonContext(
        detach_process=True,
        pidfile=PIDLockFile(PATH_PID),
        working_directory=os.getcwd(),
        signal_map={
            signal.SIGTERM: on_sigterm
        },
        stdout=sys.stdout,
        stderr=sys.stderr
    )

    try:
        logger.info("Starting PlayingWHAT Service...")

        # Determine if there's an environment variable called ENV_FILE. If so, we'll load the
        # .env file specified in the ENV_FILE path
        env_file_path = os.getenv("ENV_FILE", None)
        if os.path.exists(env_file_path):
            logger.info("Loading .env file from %s", env_file_path)
            dotenv.load_dotenv(env_file_path)
        else:
            logger.info("Loading .env file from default location")
            dotenv.load_dotenv()

        # Show some useful information about the environment variables we've loaded
        logger.debug("SPOTIFY_CLIENT_ID = %s", os.getenv("SPOTIFY_CLIENT_ID"))
        logger.debug("SPOTIFY_CLIENT_SECRET = %s", "*" * len(os.getenv("SPOTIFY_CLIENT_SECRET")))

        with context:
            asyncio.run(server.start())
    except Exception:
        logger.exception("Failed to start PlayingWHAT Service")


if __name__ == "__main__":
    main()
