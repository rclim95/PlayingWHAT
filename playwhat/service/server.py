"""Responsible for starting the `playwhat.service` server"""

import asyncio
from datetime import timedelta
import json
import os
import time
import spotipy
import playwhat
from playwhat.service import LOGGER
from playwhat.service.constants import PATH_UNIX_SOCKET
import playwhat.service.messages as messages
from playwhat.painter import display, PainterOptions, DeviceType, RepeatStatus

_SERVER: asyncio.AbstractServer = None
_POLLER: asyncio.Task = None

async def on_client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Called when a client has connected to the daemon server"""
    LOGGER.info("Client connected")

    # Record the current time so we can measure how long it took to process the request
    start_time = time.time()

    handler = messages.DefaultHandler
    request = await handler.read(reader)
    if request is None:
        LOGGER.debug("Got unexpected message, ignoring")
    elif isinstance(request, messages.UpdateDisplayMessage):
        # Check to see if the message we're updating
        LOGGER.info("Received UpdateDisplayMesasge with parameters: %s",
                    json.dumps(request.to_json()))
        options = request.to_painter_options()

        # Should we update?
        LOGGER.info("Updating InkyWHAT screen...")
        display(options)

    # We're done
    end_time = time.time()
    LOGGER.info("Request handled successfully (took %0.0f seconds)", round(end_time - start_time))
    await handler.write(writer, messages.ResponseMessage(succeeded=True))
    writer.close()

async def run_server():
    """Runs the server"""
    global _SERVER

    LOGGER.info("Running server...")
    try:
        server = await asyncio.start_unix_server(on_client_connected, path=PATH_UNIX_SOCKET)
        async with server:
            LOGGER.info("Unix socket created at \"%s\"", PATH_UNIX_SOCKET)
            _SERVER = server
            await server.serve_forever()
    except asyncio.CancelledError:
        LOGGER.info("Server stopped.")

async def run_poller():
    """Runs the poller for Spotify"""
    global _POLLER
    LOGGER.info("Running Spotify poller...")

    # Keep polling the Spotify API for the duration that the server is running
    while True:
        try:
            LOGGER.info("Updating PlayingWHAT with latest playback status from Spotify...")

            # Setup who we are
            user_token = os.getenv(playwhat.ENV_USER_TOKEN)
            oauth_manager = spotipy.SpotifyOAuth(
                client_id=os.getenv(playwhat.ENV_CLIENT_ID),
                client_secret=os.getenv(playwhat.ENV_CLIENT_SECRET),
                redirect_uri=os.getenv(playwhat.ENV_REDIRECT_URL),
                cache_path=os.getenv(playwhat.ENV_CREDENTIAL_CACHE_PATH),
                scope=" ".join(playwhat.API_SCOPES)
            )

            # Communicate with the Spotify API
            api_client = spotipy.Spotify(
                auth=user_token,
                oauth_manager=oauth_manager
            )

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

            display(options)

            delay = 0.0
            if current_track["is_playing"]:
                # Assume the user is going to listen to the whole track, let's check back again
                # a quarter away from the user's current progress.
                progress_ms = current_track["progress_ms"]
                duration_ms = track["duration_ms"]
                delay = ((duration_ms - progress_ms) / 4) / 1000

                # However, if the calculated delay ends up being a number smaller than 15 seconds,
                # we'll just use the duration_ms - progress_ms (no need to keep refreshing once we're
                # at the 15 seconds mark--let's assume the user will be listening to the track all the
                # way through)
                if delay <= 15.0:
                    delay = (duration_ms - progress_ms) / 1000
            else:
                # Since the user isn't playing anything, we'll check again in a minute.
                delay = 60.0

            LOGGER.info("Display updated, polling again in %0.0f seconds", delay)
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            LOGGER.info("Poller stopped.")
            break
        except Exception:
            LOGGER.exception("Failed to get update PlayingWHAT display with information from Spotify")
            LOGGER.info("Trying again in 60 seconds...")
            await asyncio.sleep(60.0)

async def start():
    """Start the service"""
    # pylint: disable=global-statement
    global _SERVER, _POLLER
    LOGGER.info("Daemon started successfully")

    _POLLER = asyncio.create_task(run_poller())

    await asyncio.gather(
        run_server(),
        _POLLER
    )

def stop():
    """Stops the server"""
    if _SERVER is not None:
        LOGGER.info("Stopping server...")
        loop = _SERVER.get_loop()
        loop.call_soon_threadsafe(_SERVER.close)

    if _POLLER is not None:
        LOGGER.info("Stopping poller...")
        _POLLER.cancel()
