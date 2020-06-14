"""The main entry point of `playwhat.console`"""

from argparse import ArgumentParser
import logging
import os
import sys
import dotenv
import spotipy
import playwhat
from playwhat.console import LOGGER

def authenticate(dotenv_path: str, args):
    """Authenticate with the Spotify API"""
    LOGGER.info("Authenticating with the Spotify API...")

    # We're going to be saving the user token into the dotenv file for future reference, so make
    # sure we can find it first before we go through the authorization process.
    if dotenv_path is None:
        try:
            dotenv_path = dotenv.find_dotenv(raise_error_if_not_found=True)
        except Exception:
            LOGGER.exception("Unable to find .ENV file. Please specify the path to the .ENV file "
                             "by setting an \"ENV_FILE\" environment variable")
            return

    # Prompt the user for their user token so we can observe what they're playing on Spotify
    #
    # TODO: Extract this to a constant.
    LOGGER.info("Prompting user for authentication...")
    scopes = ["user-read-recently-played", "user-read-playback-state"]
    cache_path = os.getenv(playwhat.ENV_CREDENTIAL_CACHE_PATH)
    token = spotipy.util.prompt_for_user_token(args.username,
                                               scope=" ".join(scopes),
                                               client_id=os.getenv(playwhat.ENV_CLIENT_ID),
                                               client_secret=os.getenv(playwhat.ENV_CLIENT_SECRET),
                                               redirect_uri=os.getenv(playwhat.ENV_REDIRECT_URL),
                                               cache_path=cache_path,
                                               show_dialog=False)

    # Save the user token for future reference
    dotenv.set_key(dotenv_path, playwhat.ENV_USER_TOKEN, token)
    LOGGER.info("User token saved to .env file, reload the service for your changes to take effect.")

def create_argparser() -> ArgumentParser:
    """Creates the argument parser for this script"""
    args = ArgumentParser(description="Provides a way to interact with the playwhat.service daemon")
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

    # Print out the environment variables being used
    dotenv_path = os.getenv("ENV_FILE", None)
    if dotenv_path is None:
        LOGGER.info("Loading .env file from default location")
        dotenv.load_dotenv()
    else:
        LOGGER.info("Loading .env file from %s", dotenv_path)
        dotenv.load_dotenv(dotenv_path)

    LOGGER.debug("SPOTIFY_CLIENT_ID = %s", os.getenv(playwhat.ENV_CLIENT_ID))
    LOGGER.debug("SPOTIFY_CLIENT_SECRET = %s", "*" * len(os.getenv(playwhat.ENV_CLIENT_SECRET)))

    # Run the action the user as speciifed
    args.func(dotenv_path, args)

if __name__ == "__main__":
    main()
