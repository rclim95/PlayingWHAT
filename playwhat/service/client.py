"""Responsible for providing a client that connects to the `playwhat.service` client"""

import asyncio
import dataclasses
import json
from playwhat.service import LOGGER
from playwhat.service.constants import PATH_UNIX_SOCKET
from playwhat.service.messages import UpdateDisplayMessage, ResponseMessage, DefaultHandler
from playwhat.service.utils import StreamMessageHandler
from playwhat.painter.types import PainterOptions

async def send_display_update(options: PainterOptions):
    """Sends a message to the `playwhat.service` server for updating the display"""
    LOGGER.info("Updating the InkyWHAT display")
    LOGGER.debug("Updating display = %s", dataclasses.asdict(options))

    # Establish a connection to Unix socket for this daemon and send the option
    handler = DefaultHandler
    reader, writer = await asyncio.open_unix_connection(PATH_UNIX_SOCKET) # type: (asyncio.StreamReader, asyncio.StreamWriter)
    await handler.write(writer, UpdateDisplayMessage.from_painter_options(options))

    # Wait for an acknowledgment from the daemon server
    response = await handler.read(reader) # type: ResponseMessage
    LOGGER.debug("Daemon server responded, succeeded = %s", response.succeeded)

    # We're done.
    writer.close()
