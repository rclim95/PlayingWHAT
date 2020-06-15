"""Responsible for providing a client that connects to the `playwhat.service` client"""

import asyncio
import dataclasses
import os

from playwhat.service import LOGGER, PATH_UNIX_SOCKET
from playwhat.service.messages import DefaultHandler, \
    ResponseMessage, \
    UpdateDisplayMessage, \
    ScreenshotMessage, \
    RefreshMessage
from playwhat.painter.types import PainterOptions

async def send_display_update(options: PainterOptions):
    """Sends a message to the `playwhat.service` server for updating the display"""
    LOGGER.info("Updating the InkyWHAT display")
    LOGGER.debug("Updating display = %s", dataclasses.asdict(options))

    # Establish a connection to Unix socket for this daemon and send the option
    handler = DefaultHandler
    reader, writer = await asyncio.open_unix_connection(PATH_UNIX_SOCKET)
    await handler.write(writer, UpdateDisplayMessage.from_painter_options(options))

    # Wait for an acknowledgment from the daemon server and then close the connection
    response = await DefaultHandler.read(reader) # type: ResponseMessage
    LOGGER.debug("Daemon server responded, succeeded = %s", response.succeeded)
    writer.close()

async def send_refresh():
    """
    Sends a message to the `playwhat.service` daemon to refreh the InkyWHAT display with the
    latest playback information as reported by the Spotify API
    """
    LOGGER.info("Sending refresh request")

    # Establish a connection to Unix socket for this daemon and send the option
    reader, writer = await asyncio.open_unix_connection(PATH_UNIX_SOCKET)
    await DefaultHandler.write(writer, RefreshMessage())

    # Wait for an acknowledgment from the daemon server and then close the connection
    response = await DefaultHandler.read(reader) # type: ResponseMessage
    LOGGER.debug("Daemon server responded, succeeded = %s", response.succeeded)
    writer.close()

async def send_screenshot_request(path: str):
    """
    Sends a message to the `playwhat.service` daemon to save a screenshot of the InkyWHAT display
    """
    # Convert the path to an absolute path (since the daemon is going to be saving the image,
    # we need to make sure path is absolute)
    path = os.path.abspath(path)

    LOGGER.info("Sending screenshot request")
    LOGGER.debug("Saving screenshot to \"%s\"", path)

    # Get the current user's UID so that when the daemon saves the image, it knows who should
    # own it.
    uid = os.getuid()
    request = ScreenshotMessage(uid, path)

    # Establish a connection to Unix socket for this daemon and send the option
    reader, writer = await asyncio.open_unix_connection(PATH_UNIX_SOCKET)
    await DefaultHandler.write(writer, request)

    # Wait for an acknowledgment from the daemon server and then close the connection
    response = await DefaultHandler.read(reader) # type: ResponseMessage
    LOGGER.debug("Daemon server responded, succeeded = %s", response.succeeded)
    writer.close()
