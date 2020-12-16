"""The main entry point of `playwhat.console`"""

from argparse import ArgumentParser, ArgumentTypeError
import asyncio
import os

import spotipy

import playwhat
from playwhat.console import LOGGER
from playwhat.service import client

def main():
    """The main entry point of this script"""
    args = _create_argparser()

    playwhat.setup_logging(args.verbose, LOGGER)
    playwhat.setup_environment_vars(LOGGER)

    # Print out some information about the environment variables that has been set
    LOGGER.debug("SPOTIFY_CLIENT_ID = %s", os.getenv(playwhat.ENV_CLIENT_ID))
    LOGGER.debug("SPOTIFY_CLIENT_SECRET = %s", "*" * len(os.getenv(playwhat.ENV_CLIENT_SECRET)))
    LOGGER.debug("SPOTIFY_USERNAME = %s", os.getenv(playwhat.ENV_USERNAME))
    LOGGER.debug("ROTATE_IMAGE = %s", os.getenv(playwhat.ENV_ROTATE_IMAGE))
    LOGGER.debug("SHOW_RECENT_TRACKS = %s", os.getenv(playwhat.ENV_SHOW_RECENT_TRACKS))

    # Run the action the user chose
    args.func(args)

def _create_argparser() -> ArgumentParser:
    args = ArgumentParser(
        prog="python3 -m playwhat.console",
        description="Enables interaction with the playwhat.service daemon"
    )
    args.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print out debug information when logging"
    )

    # Provide actions that the user can perform with playwhat.console
    actions = args.add_subparsers(
        title="Actions", help="All the actions that can be performed",
        dest="action", required=True
    )

    # "auth" provides a way for the user to authenticate with the Spotify API
    auth_action = actions.add_parser(
        "auth",
        help="Authenticate with the Spotify API so that PlayingWHAT can show what's playing"
    )
    auth_action.set_defaults(func=_do_authenticate)

    # "refresh" provides a way to force the PlayingWHAT screen to query the Spotify API to see
    # what's playing.
    refresh_action = actions.add_parser(
        "refresh",
        help="Force the InkyWHAT to show what's currently playing on Spotify"
    )
    refresh_action.set_defaults(func=_do_refresh)

    # "screenshot" provides a way to save an image ("screenshot") of what's being shown on the
    # InkyWHAT.
    screenshot_action = actions.add_parser(
        "screenshot",
        help="Save an image of what's shown on the InkyWHAT display"
    )
    screenshot_action.set_defaults(func=_do_screenshot)
    screenshot_action.add_argument(
        "output",
        type=_validate_path,
        help="The path to save the screenshot to. This must be an absolute path."
    )

    return args.parse_args()

def _do_authenticate(args): # pylint: disable=unused-argument
    # Prompt the user for their user token so we can observe what they're playing on Spotify
    LOGGER.info("Prompting user \"%s\" for authentication...", os.getenv(playwhat.ENV_USERNAME))
    cache_path = os.getenv(playwhat.ENV_CREDENTIAL_CACHE_PATH)
    spotipy.util.prompt_for_user_token(
        username=os.getenv(playwhat.ENV_USERNAME),
        scope=" ".join(playwhat.API_SCOPES),
        client_id=os.getenv(playwhat.ENV_CLIENT_ID),
        client_secret=os.getenv(playwhat.ENV_CLIENT_SECRET),
        redirect_uri=os.getenv(playwhat.ENV_REDIRECT_URL),
        cache_path=cache_path,
        show_dialog=False
    )

    # NOTE: We're not actually doing anything to save the token. Rather, we're letting spotipy
    # save the cached token to where ENV_CREDENTIAL_CACHE_PATH is so that when the service polls
    # Spotify again, it'll be able to use the (now-existing) cached credentials at that path.
    LOGGER.info(
        "User token saved to \"%s\" successfully.",
        os.getenv(playwhat.ENV_CREDENTIAL_CACHE_PATH)
    )
    LOGGER.info("Run 'systemctl reload playwhat' for the changes to take effect.")

def _do_refresh(args): # pylint: disable=unused-argument
    async def do_refresh():
        await client.send_refresh()

    asyncio.run(do_refresh())

def _do_screenshot(args):
    async def do_screenshot():
        await client.send_screenshot_request(args.output)

    asyncio.run(do_screenshot())

def _validate_path(path: str) -> str:
    # Ensure that the base path exists
    base_path = os.path.dirname(path)
    if not os.path.exists(base_path):
        raise ArgumentTypeError("The directory \"{}\" does not exist.".format(base_path))

    return path

if __name__ == "__main__":
    main()
