"""Responsible for starting the `playwhat.daemon` server"""

import asyncio
import os
import signal
import time
from playwhat.daemon import LOGGER
from playwhat.daemon.constants import PATH_PID, PATH_UNIX_SOCKET

_SERVER: asyncio.AbstractServer = None

def on_client_connected(reader, writer):
    """Called when a client has conneced to the daemon server"""
    LOGGER.info("Client connected")

def on_sigterm(signum, frame):
    """Called when the OS sends a `SIGTERM` signal"""
    if _SERVER is not None:
        loop = _SERVER.get_loop()
        loop.call_soon_threadsafe(_SERVER.close)

async def start():
    """Start the service"""
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
