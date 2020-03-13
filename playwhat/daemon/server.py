"""Responsible for starting the `playwhat.daemon` server"""

import asyncio
import json
import os
import signal
from playwhat.daemon import LOGGER
from playwhat.daemon.constants import PATH_PID, PATH_UNIX_SOCKET
import playwhat.daemon.messages as messages
from playwhat.painter import display

_SERVER: asyncio.AbstractServer = None

async def on_client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Called when a client has conneced to the daemon server"""
    LOGGER.info("Client connected")

    handler = messages.DefaultHandler
    request = await handler.read(reader)
    if request is None:
        LOGGER.debug("Got unexpected message, ignoring")
    elif isinstance(request, messages.UpdateDisplayMessage):
        LOGGER.info("Updating the InkyWHAT display (this will take a few seconds)")
        LOGGER.debug("Updating display with parameters: %s", json.dumps(request.to_json()))
        options = request.to_painter_options()
        display(options)

    # We're done
    LOGGER.info("Request handled successfully")
    await handler.write(writer, messages.ResponseMessage(succeeded=True))
    writer.close()

def on_sigterm(signum, frame):
    """Called when the OS sends a `SIGTERM` signal"""
    # pylint: disable=unused-argument
    if _SERVER is not None:
        loop = _SERVER.get_loop()
        loop.call_soon_threadsafe(_SERVER.close)

async def start():
    """Start the service"""
    # pylint: disable=global-statement
    global _SERVER
    LOGGER.info("Daemon started successfully")

    # Register so that we properly handle the SIGTERM
    signal.signal(signal.SIGTERM, on_sigterm)

    # Start the server
    try:
        server = await asyncio.start_unix_server(on_client_connected, path=PATH_UNIX_SOCKET)
        async with server:
            LOGGER.info("Unix socket created at \"%s\"", PATH_UNIX_SOCKET)
            _SERVER = server
            await server.serve_forever()
    except asyncio.CancelledError:
        LOGGER.info("Unix socket stopped successfully")

    # Delete the PID file since we've terminated
    LOGGER.info("Terminating daemon...")
    os.remove(PATH_PID)
