"""The main file that is executed for the `playwhat.daemon` package"""

from argparse import ArgumentParser, FileType
import asyncio
import logging
import logging.config
import os
import signal
import sys
from playwhat.daemon import LOGGER, server
from playwhat.daemon.constants import PATH_PID

def parse_arguments() -> ArgumentParser:
    """Parse the arguments that were passed"""
    args = ArgumentParser("playwhat.daemon", description="PlayWHAT Daemon")
    args.add_argument("--log-level",
                      help="The logging level.",
                      choices=[logging.DEBUG, logging.INFO, logging.WARN, logging.ERROR],
                      default=logging.INFO)
    args.add_argument("--log-config",
                      help="The path to the log configuration file",
                      metavar="config",
                      type=FileType("r"))

    # Add a subparsers for storing actions
    subparsers = args.add_subparsers(help="Available actions",
                                     dest="action",
                                     metavar="action",
                                     required=True)

    start_args = subparsers.add_parser("start", help="Start the daemon")
    start_args.set_defaults(execute=start)

    stop_args = subparsers.add_parser("stop", help="Stop the daemon")
    stop_args.set_defaults(execute=stop)

    return args.parse_args()

def start(args):
    """Start the daemon"""
    LOGGER.info("Starting playwhat.daemon...")

    try:
        # Fork the process so that we can start the daemon.
        pid = os.fork()

        # Are we the forked child process?
        if pid == 0:
            # We can start the daemon server now.
            asyncio.run(server.start())
            return
    except OSError:
        # Something went wrong.
        LOGGER.exception("Failed to fork daemon")

    # Write the PID file
    try:
        with open(PATH_PID, "w") as pid_file:
            print(pid, file=pid_file)

        # We're done.
        LOGGER.info("Daemon forked successfully, PID = %d", pid)
    except OSError:
        # Fatal error while attempting to write the PID file
        LOGGER.exception("Failed to create PID file \"%s\"", PATH_PID)

def stop(args):
    """Stop the daemon"""
    LOGGER.info("Stopping playwhat.daemon...")

    # Open the PID file that contains the PID of the daemon so we can send a SIGTERM signal to it
    with open(PATH_PID, "r") as pid_file:
        pid = int(pid_file.read().strip())
        os.kill(pid, signal.SIGTERM)

def main():
    """The main entry point"""
    args = parse_arguments()

    # Setup logging, if specified
    if args.log_config is not None:
        logging.config.fileConfig(args.log_config,
                                  disable_existing_loggers=False)
    else:
        # Set up basic logging that prints out to the STDOUT.
        logging.basicConfig(level=args.log_level,
                            format="[%(levelname)s] %(asctime)s - %(name)s: %(message)s",
                            stream=sys.stdout)

    args.execute(args)

if __name__ == "__main__":
    main()
