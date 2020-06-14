"""Provide utility functions for the `playwhat.service` module"""

from asyncio import StreamReader, StreamWriter
from datetime import timedelta
import json
from json import JSONEncoder, JSONDecodeError
import warnings
from playwhat.service import LOGGER

class CustomJsonEncoder(JSONEncoder):
    """Provides a custom JSON encoder for the `playwhat.service`"""

    def default(self, o): # pylint: disable=method-hidden
        """Converts `obj` into something JSON serializable"""
        if isinstance(o, timedelta):
            return o.total_seconds()

        return JSONEncoder.default(self, o)

class MessageHandler:
    """Provide a way for reading and writing messages"""

    def __init__(self):
        self.handlers = {}

    def register(self, cls):
        """
        Registers a class with the message handler.

        The class `cls` should have the following:
        ```python
        class MyMessage:
            MessageID: int

            @classmethod
            def from_json(cls, message):
                # TODO: Read the message returned from JSON.
                pass

            def to_json(self):
                # TODO: Return this message into a JSON-serializable object.
                pass
        ```
        """
        self.handlers[cls.MessageID] = cls
        return cls

    def read_message(self, message_id: int, message: str):
        """
        Reads a message of type `message_id` from the provided `message` and returns the processed
        message
        """
        try:
            handler = self.handlers[message_id]

            return handler.from_json(json.loads(message))
        except KeyError:
            warnings.warn("Unknown message ID \"{}\"".format(message_id))
        except TypeError as error:
            warnings.warn("Message does not meet the protocol ({})".format(str(error)))
        except JSONDecodeError as error:
            warnings.warn("Unable to decode message ({})".format(str(error)))

    def write_message(self, message):
        """Writes a message and returns the message as a JSON"""
        try:
            return json.dumps(message.to_json())
        except TypeError as error:
            warnings.warn("Message does not meet the protocol ({})".format(error))
        except JSONDecodeError as error:
            warnings.warn("Unable to encode message ({})".format(str(error)))

class StreamMessageHandler(MessageHandler):
    """
    Provides a `MessageHandler` that can read/write messages from `asyncio.StreamReader` and
    `asyncio.StreamWriter`.
    """

    async def read(self, reader: StreamReader):
        """Reads a message from a stream and return it"""
        # The message should start off with SOH (start of heading)
        soh = await reader.read(1)
        if soh != b'\x01':
            # I don't know how to process this.
            warnings.warn("Unknown message in stream (0x01 not found)")
            return

        # The next part should be the message ID follow by STX (start of text). Keep reading
        # until we come across STX.
        message_id_bytes = await reader.readuntil(b'\x02')
        message_id = int.from_bytes(message_id_bytes[:-1], "big", signed=False)
        LOGGER.debug("Parsed message ID = %d", message_id)

        # The next part should be the message follow by EOT (end of transmission). Keep reading
        # until we come across EOT
        message_bytes = await reader.readuntil(b'\04')
        message_str = message_bytes[:-1].decode("utf-8")
        LOGGER.debug("Parsed message = %s", message_str)

        try:
            # The message should be in valid JSON, so parse it.
            return self.read_message(message_id, message_str)
        except json.JSONDecodeError as error:
            # I don't know how to process this message.
            warnings.warn("Unknown JSON message in stream ({})".format(str(error)))
            return None

    async def write(self, writer: StreamWriter, message):
        """Writes a message to a `StreamWriter`"""
        # The message should have a message ID
        message_id = message.MessageID # type: int
        message = self.write_message(message)

        # Encode the message that we're ready to write
        data = [
            b'\x01',                        # SOH (start of heading)
            message_id.to_bytes(4, "big"), # Message ID (4 bytes)
            b'\x02',                        # SOT (start of text)
            message.encode("utf-8"),       # Message
            b'\x04'                         # EOT (end of transmission)
        ]

        # Wait for the writer to finish
        writer.write(b"".join(data))
        await writer.drain()
