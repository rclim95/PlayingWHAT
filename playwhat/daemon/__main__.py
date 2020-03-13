"""The main file that is executed for the `playwhat.daemon` package"""

from argparse import ArgumentParser, FileType
import asyncio
from datetime import timedelta
import logging
import logging.config
import os
import signal
import sys
from playwhat.daemon import LOGGER, server, client
from playwhat.daemon.constants import PATH_PID
from playwhat.painter.types import DeviceType, RepeatStatus, PainterOptions

def parse_arguments() -> ArgumentParser:
    """Parse the arguments that were passed"""
    args = ArgumentParser("playwhat.daemon", description="PlayWHAT Daemon")
    args.add_argument("--log-level",
                      help="The logging level.",
                      choices=[logging.DEBUG, logging.INFO, logging.WARN, logging.ERROR],
                      type=int,
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

    update_args = subparsers.add_parser("update", help="Update the InkyWHAT display")
    update_args.add_argument("--playing",
                             help="Pass this to indicate that music is playing",
                             action="store_true")
    update_args.add_argument("--shuffle",
                             help="Pass this to indicate that shuffle is on",
                             action="store_true")
    update_args.add_argument("--repeat",
                             help="The repeat status",
                             type=RepeatStatus.from_string,
                             choices=list(RepeatStatus),
                             default=RepeatStatus.OFF)
    update_args.add_argument("--album-art-url",
                             help="The URL to the album art",
                             required=True,
                             metavar="url")
    update_args.add_argument("--album-name",
                             help="The name of the album",
                             metavar="name")
    update_args.add_argument("--track-duration",
                             help="How long the track is (in seconds)",
                             type=int,
                             required=True,
                             metavar="secs")
    update_args.add_argument("--track-name",
                             help="The name of the track",
                             required=True,
                             metavar="name")
    update_args.add_argument("--artist-name",
                             help="The name of the artist",
                             required=True,
                             metavar="name")
    update_args.add_argument("--user-picture-url",
                             help="The URL to the user's picture",
                             required=True,
                             metavar="url")
    update_args.add_argument("--user-name",
                             help="The name of the user",
                             required=True,
                             metavar="name")
    update_args.add_argument("--device",
                             help="The device that the user is streaming their music from",
                             type=DeviceType.from_string,
                             choices=list(DeviceType),
                             default=DeviceType.OTHER)
    update_args.add_argument("--device-name",
                             help="The name of the device",
                             required=True,
                             metavar="name")
    update_args.set_defaults(execute=update)

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

def update(args):
    """Update the InkyWHAT display"""
    options = PainterOptions(
        artist_name=args.artist_name,
        album_name=args.album_name,
        album_image_url=args.album_art_url,
        device_name=args.device_name,
        device_type=args.device,
        duration=timedelta(seconds=args.track_duration),
        is_playing=args.playing,
        is_shuffled=args.shuffle,
        repeat_status=args.repeat,
        track_name=args.track_name,
        user_name=args.user_name,
        user_image_url=args.user_picture_url
    )
    asyncio.run(client.send_display_update(options))

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
