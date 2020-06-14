"""The main entry point of `playwhat.console`"""

from argparse import ArgumentParser
import asyncio
from datetime import timedelta
import json
import logging
import os
import sys
import dotenv
import spotipy
import playwhat
from playwhat.console import LOGGER
from playwhat.service.client import send_display_update
from playwhat.painter.types import DeviceType, RepeatStatus, PainterOptions

def authenticate(dotenv_path: str, args):
    """Authenticate with the Spotify API"""
    LOGGER.info("Authenticating with the Spotify API...")

    # We're going to be saving the user token into the dotenv file for future reference, so make
    # sure we can find it first before we go through the authorization process.
    if dotenv_path is None:
        try:
            dotenv_path = dotenv.find_dotenv(raise_error_if_not_found=True)
        except IOError:
            LOGGER.exception("Unable to find .ENV file. Please specify the path to the .ENV file "
                             "by setting an \"ENV_FILE\" environment variable")
            return

    # Prompt the user for their user token so we can observe what they're playing on Spotify
    #
    # TODO: Extract this to a constant.
    LOGGER.info("Prompting user for authentication...")
    cache_path = os.getenv(playwhat.ENV_CREDENTIAL_CACHE_PATH)
    token = spotipy.util.prompt_for_user_token(args.username,
                                               scope=" ".join(playwhat.API_SCOPES),
                                               client_id=os.getenv(playwhat.ENV_CLIENT_ID),
                                               client_secret=os.getenv(playwhat.ENV_CLIENT_SECRET),
                                               redirect_uri=os.getenv(playwhat.ENV_REDIRECT_URL),
                                               cache_path=cache_path,
                                               show_dialog=False)

    # Save the user token for future reference
    dotenv.set_key(dotenv_path, playwhat.ENV_USER_TOKEN, token)
    LOGGER.info("User token saved to .env file, reload the service for changes to take effect.")

def refresh(dotenv_path: str, args):
    """Refresh the PlayingWHAT display with what's playing on the user's Spotify"""

    async def do_update():
        LOGGER.info("Refreshing the PlayingWHAT display...")

        # Talk to the Spotify API and see what's the user is playing and who they are
        oauth_manager = spotipy.SpotifyOAuth(client_id=os.getenv(playwhat.ENV_CLIENT_ID),
                                            client_secret=os.getenv(playwhat.ENV_CLIENT_SECRET),
                                            redirect_uri=os.getenv(playwhat.ENV_REDIRECT_URL),
                                            cache_path=os.getenv(playwhat.ENV_CREDENTIAL_CACHE_PATH),
                                            scope=" ".join(playwhat.API_SCOPES))
        api_client = spotipy.Spotify(auth=os.getenv(playwhat.ENV_USER_TOKEN), 
                                    oauth_manager=oauth_manager)

        # Now that we know what track the user is playing, build the UpdateDisplayMessage so that
        # we can update the display.
        current_user = api_client.current_user()
        current_track = api_client.current_playback()
        LOGGER.debug("The user is currently playing: %s", json.dumps(current_track))

        track = current_track["item"]
        if track is None:
            LOGGER.warning("The track could not be found. Is the user in private mode?")
            return

        device_type = DeviceType.OTHER
        current_device = current_track["device"]["type"]
        if current_device == "Computer":
            device_type = DeviceType.COMPUTER
        elif current_device == "Smartphone":
            device_type = DeviceType.PHONE
        elif current_device == "TV":
            device_type = DeviceType.TV
        elif current_device == "Speaker":
            device_type = DeviceType.SPEAKER

        repeat_type = RepeatStatus.OFF
        current_repeat = current_track["repeat_state"]
        if current_repeat == "track":
            repeat_type = RepeatStatus.SINGLE
        elif current_repeat == "context":
            repeat_type = RepeatStatus.ALL

        options = PainterOptions(
            artist_name=track["artists"][0]["name"],
            album_name=track["album"]["name"],
            album_image_url=track["album"]["images"][0]["url"],
            device_name=current_track["device"]["name"],
            device_type=device_type,
            duration=timedelta(milliseconds=track["duration_ms"]),
            is_playing=current_track["is_playing"],
            is_shuffled=current_track["shuffle_state"],
            repeat_status=repeat_type,
            track_name=track["name"],
            user_name=current_user["display_name"],
            user_image_url=current_user["images"][0]["url"]
        )

        await send_display_update(options)

    asyncio.run(do_update())

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

    refresh_action = actions.add_parser("refresh", help="Refresh the PlayingWHAT display")
    refresh_action.set_defaults(func=refresh)

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
