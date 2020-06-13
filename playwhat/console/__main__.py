"""The main entry point of `playwhat.console`"""

from argparse import ArgumentParser
import logging
import os
import sys
import dotenv
import spotipy

def authenticate(args):
    """Authenticate with the Spotify API"""
    logger = logging.getLogger()
    logger.info("Authenticating with the Spotify API...")

    # We're going to be saving the user token into the dotenv file for future reference, so make
    # sure we can find it first before we go through the authorization process.
    dotenv_path = args.dotenv
    if dotenv_path is None:
        try:
            dotenv_path = dotenv.find_dotenv(raise_error_if_not_found=True)
        except Exception:
            logger.exception("Unable to find .ENV file. Please specify the path to the .ENV file "
                             "using the --dotenv switch.")
            return

    # Prompt the user for their user token so we can observe what they're playing on Spotify
    #
    # TODO: Extract this to a constant.
    logger.info("Prompting user for authentication...")
    scopes = ["user-read-recently-played", "user-read-playback-state"]
    cache_path = os.getenv("SPOTIFY_CREDENTIAL_CACHE_PATH")
    token = spotipy.util.prompt_for_user_token(args.username,
                                               scope=" ".join(scopes),
                                               client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                                               client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
                                               redirect_uri=os.getenv("SPOTIFY_REDIRECT_URL"),
                                               cache_path=cache_path,
                                               show_dialog=False)

    # Save the user token for future reference
    dotenv.set_key(dotenv_path, "SPOTIFY_USER_TOKEN", token)
    logger.info("User token saved to .env file, restart the service for your changes to take effect.")

def create_argparser() -> ArgumentParser:
    """Creates the argument parser for this script"""
    args = ArgumentParser(description="Provides a way to interact with the playwhat.service daemon")
    args.add_argument("--dotenv", metavar="file", help="The path to the .env file to load.")
    args.add_argument("-v", "--verbose", action="store_true", help="Print out debug information.")

    actions = args.add_subparsers(
        title="Actions",
        help="All the actions that can be performed",
        dest="action",
        required=True)

    auth_action = actions.add_parser("auth", help="Authenticate with the Spotify API")
    auth_action.set_defaults(func=authenticate)
    auth_action.add_argument("username", help="The Spotify username to authenticate as")

    return args.parse_args()

def main():
    """The main entry point of this script"""
    args = create_argparser()

    # Set up basic logging that prints out to the STDOUT.
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
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

    # Run the action the user as speciifed
    args.func(args)

if __name__ == "__main__":
    main()
