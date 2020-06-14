"""Responsible for starting the `playwhat.service` server"""

import asyncio
import json
import time
from playwhat.service import LOGGER
from playwhat.service.constants import PATH_UNIX_SOCKET
import playwhat.service.messages as messages
from playwhat.painter import display, PainterOptions

_SERVER: asyncio.AbstractServer = None

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

async def start():
    """Start the service"""
    # pylint: disable=global-statement
    global _SERVER
    LOGGER.info("Daemon started successfully")

    # Start the server
    try:
        server = await asyncio.start_unix_server(on_client_connected, path=PATH_UNIX_SOCKET)
        async with server:
            LOGGER.info("Unix socket created at \"%s\"", PATH_UNIX_SOCKET)
            _SERVER = server
            await server.serve_forever()
    except asyncio.CancelledError:
        LOGGER.info("Unix socket stopped successfully")

def stop():
    """Stops the server"""
    if _SERVER is not None:
        loop = _SERVER.get_loop()
        loop.call_soon_threadsafe(_SERVER.close)
