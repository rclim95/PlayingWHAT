"""The main entry point of `playwhat.console`"""

from argparse import ArgumentParser
import dotenv
import logging
import os
import sys

def create_argparser() -> ArgumentParser:
    """Creates the argument parser for this script"""
    args = ArgumentParser(description="Provides a way to interact with the playwhat.service daemon")
    args.add_argument("--dotenv", metavar="file", help="The path to the .env file to load.")
    args.add_argument("-v", "--verbose", action="store_true",  help="Print out debug information.")

    return args.parse_args()

def main():
    """The main entry point of this script"""
    args = create_argparser()

    # Set up basic logging that prints out to the STDOUT.
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARN,
                        format="[%(levelname)s] %(asctime)s - %(name)s: %(message)s",
                        stream=sys.stdout)
    logger = logging.getLogger()

    # Print out the environment variables being used
    if args.dotenv is None:
        logger.info("Loading .env file from default location")
        dotenv.load_dotenv()
    else:
        logger.info("Loading .env file from %s", args.dotenv)
        dotenv.load_dotenv(args.dotenv)

    logger.debug("SPOTIFY_CLIENT_ID = %s", os.getenv("SPOTIFY_CLIENT_ID"))
    logger.debug("SPOTIFY_CLIENT_SECRET = %s", "*" * len(os.getenv("SPOTIFY_CLIENT_SECRET")))

if __name__ == "__main__":
    main()
