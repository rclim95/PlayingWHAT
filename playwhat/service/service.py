"""Contains functionalities for starting, running, and stopping the `playwhat.service` service"""

import asyncio
from asyncio import AbstractServer, Task, CancelledError, StreamReader, StreamWriter
from datetime import timedelta
import json
import os
from socket import socket
from time import time

import spotipy

import playwhat
from playwhat.painter import display, \
    display_not_playing, \
    save_screenshot
from playwhat.painter.types import PainterOptions, \
    RepeatStatus, \
    DeviceType
from playwhat.service import LOGGER, PATH_UNIX_SOCKET
from playwhat.service.messages import DefaultHandler, \
    UpdateDisplayMessage, \
    ResponseMessage, \
    ScreenshotMessage, \
    RefreshMessage

_server: AbstractServer = None
_poller: Task = None
_user = None

async def start():
    """Starts the service"""
    _poller = asyncio.create_task(_do_run_poller())

    try:
        await asyncio.gather(
            _do_run_command_server(),
            _poller
        )
    except CancelledError:
        # The user has requested to cancel. That implies that the service has been stopped.
        LOGGER.info("Service stop has been requested.")

def reload():
    """Reloads the configuration for the service"""
    global _user

    # Setup the logging again
    LOGGER.info("Reloading logging information")
    playwhat.setup_logging(logger=LOGGER)

    # Setup the environment variables again
    LOGGER.info("Reloading environment variables from .ENV file...")
    playwhat.setup_environment_vars(logger=LOGGER)

    # Show some useful information about the environment variables we've loaded
    LOGGER.info("Environment variables reloaded")
    LOGGER.debug("SPOTIFY_CLIENT_ID = %s", os.getenv(playwhat.ENV_CLIENT_ID))
    LOGGER.debug("SPOTIFY_CLIENT_SECRET = %s", "*" * len(os.getenv(playwhat.ENV_CLIENT_SECRET)))
    LOGGER.debug("SPOTIFY_USERNAME = %s", os.getenv(playwhat.ENV_USERNAME))

    # Reset the _user variable, so that the next time we're polling Spotify, we get fresh information
    # about the user logged in
    _user = None

    # Success!
    LOGGER.info("Reloaded .env successfully")

def stop():
    """Stops the service"""
    if _server is not None:
        LOGGER.info("Stopping command server")
        loop = _server.get_loop()
        loop.call_soon_threadsafe(_server.close)

    if _poller is not None:
        LOGGER.info("Stopping poller")
        _poller.cancel()

def _create_client() -> spotipy.Spotify:
    # Setup who we are
    oauth_manager = spotipy.SpotifyOAuth(
        client_id=os.getenv(playwhat.ENV_CLIENT_ID),
        client_secret=os.getenv(playwhat.ENV_CLIENT_SECRET),
        redirect_uri=os.getenv(playwhat.ENV_REDIRECT_URL),
        cache_path=os.getenv(playwhat.ENV_CREDENTIAL_CACHE_PATH),
        username=os.getenv(playwhat.ENV_USERNAME),
        scope=" ".join(playwhat.API_SCOPES)
    )
    user_token = oauth_manager.get_access_token(as_dict=False)
    if user_token is None:
        # The user hasn't authenticated with the Spotify API. Tell them that they must
        # authenticate in order to continue.
        LOGGER.error(
            "A user has not authenticated with the Spotify API, so no playback "
            "information can be shown at this time."
        )
        LOGGER.info(
            "Please authenticate with the Spotify API at least once by running the "
            "following command:\n"
            "$ python3 -m playwhat.console auth <spotify-username>"
        )
        return None

    return spotipy.Spotify(auth=user_token, oauth_manager=oauth_manager)

async def _handle_request(reader: StreamReader, writer: StreamWriter):
    """Handles the incoming request"""
    request = await DefaultHandler.read(reader)
    succeeded = True

    if request is None:
        LOGGER.info("Client sent unexpected message, ignoring.")
        succeeded = False
    elif isinstance(request, UpdateDisplayMessage):
        LOGGER.info("Client sent UpdateDisplayMessage, parameters = %s",
                    json.dumps(request.to_json()))

        # Update the display
        LOGGER.info("Updating InkyWHAT display")
        options = request.to_painter_options()
        display(options)

        succeeded = True
    elif isinstance(request, ScreenshotMessage):
        LOGGER.info("Client sent ScreenshotMessage, parameters = %s",
                    json.dumps(request.to_json()))

        LOGGER.info("Saving InkyWHAT screenshot to %s", request.output_path)
        save_screenshot(request.output_path, request.uid)

        succeeded = True
    elif isinstance(request, RefreshMessage):
        LOGGER.info("Client sent RefreshMessage")
        succeeded = _handle_refresh_message()


    # Write the result and close the connection
    LOGGER.info("Request handled, succeeded = %s", succeeded)
    await DefaultHandler.write(writer, ResponseMessage(succeeded))
    writer.close()

def _handle_refresh_message():
    global _user

    # Communicate with the Spotify API and start getting information about their
    # currently played track
    api_client = _create_client()
    if api_client is None:
        # Something went wrong.
        return False

    # Get the current playback
    playback = api_client.current_playback()

    # As well as information about the user that's logged into Spotify (note that we cache
    # the result so that we're not calling this endpoint every time--it's unlikely the
    # information returned by api_client.me() will be changing constantly)
    if _user is None:
        _user = api_client.me()

    # Let's update!
    _update_display(_user, playback)
    return True

async def _on_client_connected(reader: StreamReader, writer: StreamWriter):
    """Called when a client has connected to the daemon server"""
    # Get information on the socket that has just connected
    peername = writer.get_extra_info("peername") # type: socket
    if peername is not None:
        LOGGER.info("Client \"%s\" connected", peername)
    else:
        LOGGER.info("Client connected")

    # Let's handle the request
    start_time = time()
    await _handle_request(reader, writer)
    end_time = time()

    LOGGER.info("Request handled in %0.0f seconds", round(end_time - start_time))

async def _do_run_command_server():
    """Runs the command server"""
    global _server # pylint: disable=invalid-name,global-statement

    LOGGER.info("Starting command server...")

    _server = await asyncio.start_unix_server(_on_client_connected, path=PATH_UNIX_SOCKET)
    async with _server:
        LOGGER.info("Command server is listening on \"%s\"", PATH_UNIX_SOCKET)
        await _server.serve_forever()

async def _do_run_poller():
    """Runs the poller"""
    global _server, _user # pylint: disable=invalid-name,global-statement

    LOGGER.info("Starting poller...")

    last_song = None
    fibonacci_iter = _fibonnaci()
    while True:
        delay_sec = 60.0
        try:
            LOGGER.info("Updating InkyWHAT with latest playback status from Spotify")

            # Communicate with the Spotify API and start getting information about their
            # currently played track
            api_client = _create_client()
            if api_client is None:
                # Something went wrong. Poll again later.
                #
                # NOTE: Since we're in a try/except/finally block, the finally block will ensure
                # that we'll delay our poll before proceeding.
                continue

            # Get the current playback
            playback = api_client.current_playback()

            # As well as information about the user that's logged into Spotify (note that we cache
            # the result so that we're not calling this endpoint every time--it's unlikely the
            # information returned by api_client.me() will be changing constantly)
            if _user is None:
                _user = api_client.me()

            # Update the screen. Note that we're recording how long it took to refresh the screen
            # so that we take that into consideration while figuring out how much longer until
            # the user has finished the track (assuming no skipping).
            start_time = time()
            _update_display(_user, playback)
            end_time = time()
            refresh_sec = end_time - start_time

            if playback is not None and playback["is_playing"]:
                # Calculate the duration remaining (including the time it took to refresh the
                # screen) so we can determine whether we should use Fibonnaci delays or the time
                # remaining.
                track = playback["item"]
                remaining = \
                    timedelta(milliseconds=track["duration_ms"] - playback["progress_ms"]) - \
                    timedelta(seconds=refresh_sec)
                LOGGER.debug("%s remaining for the current track", str(remaining))

                # Is this a different song being played?
                if track["id"] != last_song:
                    # Yup, it's a new song. In that case, we should reset our Fibonnaci series.
                    #
                    # Note that we're using Fibonnaci to figure out when to poll again. We're
                    # operating under the assumption that the user will most likely skip within the
                    # first half of the song, but decrease that chance as the song continues playing
                    #
                    # Interesting tidbits:
                    # https://musicmachinery.com/2014/05/02/the-skip/
                    fibonacci_iter = _fibonnaci()
                    last_song = track["id"]

                # Get the next number in our Fibonnaci series
                next_fibonnaci = next(fibonacci_iter)

                # Will we exceed the length of the song if we were to delay another Fibonnaci
                # series?
                if remaining - timedelta(seconds=next_fibonnaci) <= timedelta(seconds=0):
                    # Use the time remaining to figure out when to skip to the next track. We'll
                    # assume the user will play this music to the end.
                    delay_sec = remaining.total_seconds()
                else:
                    delay_sec = next_fibonnaci
            else:
                # The user isn't playing anything. We'll check again in 30 seconds.
                delay_sec = 30.0
        except Exception: # pylint: disable=broad-except
            LOGGER.exception("Failed to update InkyWHAT with latest playback info from Spotify")
        finally:
            # Ensure that delay_sec is a number > 0, so that we're not polling again immediately.
            delay_sec = max(delay_sec, 1)

            # Now to wait...
            LOGGER.info("Polling Spotify API again in %0.0f seconds", delay_sec)
            await asyncio.sleep(delay_sec)

def _fibonnaci():
    # pylint: disable=invalid-name
    a, b = 0, 1
    while True:
        c = a + b
        a = b
        b = c
        yield c

def _update_display(current_user, playback):
    if playback is None:
        LOGGER.info("The user is not playing anything.")

        start_time = time()
        display_not_playing()
        end_time = time()

        refresh_sec = end_time - start_time
        LOGGER.debug("Refreshing the InkyWHAT screen took %0.0f seconds", refresh_sec)
        return True
    else:
        current_item = playback["item"]
        if current_item is None:
            LOGGER.warning("The current item is not available. Is the user in private mode?")
            return False

        if current_item["type"] != "track":
            LOGGER.warning("The current item is not a track object. Tracks are only supported.")
            return False

        # Build the PainterOptions that'll pass to the painter and display it
        device = playback["device"]
        track = playback["item"]
        album = track["album"]
        artists = track["artists"]
        options = PainterOptions(
            artist_name="; ".join(map(lambda artist: artist["name"], artists)),
            album_name=album["name"],
            album_image_url=album["images"][0]["url"],
            device_name=device["name"],
            device_type=DeviceType.from_api(device["type"]),
            duration=timedelta(milliseconds=track["duration_ms"]),
            is_playing=True,
            is_shuffled=playback["shuffle_state"],
            repeat_status=RepeatStatus.from_api(playback["repeat_state"]),
            track_name=track["name"],
            user_name=current_user["display_name"],
            user_image_url=current_user["images"][0]["url"]
        )

        start_time = time()
        display(options)
        end_time = time()

        refresh_sec = end_time - start_time
        LOGGER.debug("Refreshing the InkyWHAT screen took %0.0f seconds", refresh_sec)
