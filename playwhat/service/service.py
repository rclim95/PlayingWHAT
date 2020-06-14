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
from playwhat.painter import display, save_screenshot, PainterOptions, RepeatStatus, DeviceType
from playwhat.service import LOGGER, PATH_UNIX_SOCKET
from playwhat.service.messages import DefaultHandler, UpdateDisplayMessage, ResponseMessage, \
    ScreenshotMessage

_server: AbstractServer = None
_poller: Task = None

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
    LOGGER.debug("SPOTIFY_USER_TOKEN = %s", "*" * len(os.getenv(playwhat.ENV_USER_TOKEN)))

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

    # Write the result and close the connection
    LOGGER.info("Request handled, succeeded = %s", succeeded)
    await DefaultHandler.write(writer, ResponseMessage(succeeded))
    writer.close()

async def _on_client_connected(reader: StreamReader, writer: StreamWriter):
    """Callced when a client has connected to the daemon server"""
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
    LOGGER.info("Starting poller...")

    while True:
        remaining = timedelta()
        has_error = False
        try:
            LOGGER.info("Updating InkyWHAT with latest playback status from Spotify")

            # Setup who we are
            oauth_manager = spotipy.SpotifyOAuth(
                client_id=os.getenv(playwhat.ENV_CLIENT_ID),
                client_secret=os.getenv(playwhat.ENV_CLIENT_SECRET),
                redirect_uri=os.getenv(playwhat.ENV_REDIRECT_URL),
                cache_path=os.getenv(playwhat.ENV_CREDENTIAL_CACHE_PATH),
                scope=" ".join(playwhat.API_SCOPES)
            )
            user_token = oauth_manager.get_access_token(as_dict=False)

            # Communicate with the Spotify API and start getting information about their
            # currently played track
            api_client = spotipy.Spotify(auth=user_token, oauth_manager=oauth_manager)
            playback = api_client.current_playback()

            # Make sure that the user is playing something. If playback is none, then that means
            # the user isn't playing anything. If there is no "item", this implies that the user is 
            # probably in private mode. Also make sure that the "item" is a track.
            if playback is None:
                LOGGER.warning("No playback state is available. The user isn't playing anything.")
                has_error = True
                continue

            current_item = playback["item"]
            if current_item is None:
                LOGGER.warning("The current item is not available. Is the user in private mode?")
                has_error = True
                continue

            if current_item["type"] != "track":
                LOGGER.warning("The current item is not a track object. Tracks are only supported.")
                has_error = True
                continue

            # Get information about the current user so that we can show their information on the
            # InkyWHAT display
            me = api_client.current_user() # pylint: disable=invalid-name

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
                is_playing=playback["is_playing"],
                is_shuffled=playback["shuffle_state"],
                repeat_status=RepeatStatus.from_api(playback["repeat_state"]),
                track_name=track["name"],
                user_name=me["display_name"],
                user_image_url=me["images"][0]["url"]
            )
            display(options)

            # Calculate the duration remaining
            remaining = timedelta(milliseconds=track["duration_ms"] - playback["progress_ms"])
        except Exception: # pylint: disable=broad-except
            LOGGER.exception("Failed to update InkyWHAT with latest playback info from Spotify")
            has_error = True
        finally:
            delay_sec: float = 0

            # Idle the loop, which will be dependent on (1) have we encountered an error or (2)
            # what's the amount of time remaining on the current track playing?
            if has_error:
                # By default, we'll try again in another minute
                delay_sec = 60
            else:
                # Otherwise, use the time remaining to figure out the delay.
                #
                # Let's assume the user may switch to the next track a quarter of the way from
                # where they're currently listening. That's when we'll poll the Spotify API for
                # the playback state.
                #
                # However, if that quarter ends up being <= 15 seconds, we'll assume the user
                # we'll listen all the way to the end of said track (cap to a maximum of 15 seconds)
                delay_sec = remaining.total_seconds() / 4
                if delay_sec <= 15:
                    # Note that we do a max(remaining.total_seconds(), ...) so that if the total
                    # seconds is 0 seconds, we'll just wait another second (instead of trying to
                    # poll immediately after by doing delay_sec = 0).
                    delay_sec = min(max(remaining.total_seconds(), 1), 15.0)

            LOGGER.info("Polling again in %0.0f seconds", delay_sec)
            await asyncio.sleep(delay_sec)
