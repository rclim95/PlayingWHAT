"""The main file that is executed for the `playwhat.service` package"""

import asyncio
import logging
import os
import signal
import sys
import daemon
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
        with context:
            asyncio.run(server.start())
    except Exception:
        logger.exception("Failed to start PlayingWHAT Service")


if __name__ == "__main__":
    main()
