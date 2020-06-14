"""Include messages that can be sent to the `playwhat.service` server"""

from datetime import timedelta
from playwhat.service.utils import StreamMessageHandler
from playwhat.painter.types import PainterOptions

ID_RESPONSE = 0
ID_UPDATE_DISPLAY = 1
ID_SCREENSHOT = 2

DefaultHandler = StreamMessageHandler() # pylint: disable=invalid-name

@DefaultHandler.register
class ResponseMessage:
    """Represents a generic response"""
    MessageID = ID_RESPONSE

    def __init__(self, succeeded: bool):
        """Constructor"""
        self.succeeded = succeeded

    @classmethod
    def from_json(cls, message):
        """Creates a `ResponseMessage` from the provided JSON"""
        return cls(message["succeeded"])

    def to_json(self):
        """Returns a `ResponseMessage` that can be serialized to JSON"""
        return {
            "succeeded": self.succeeded
        }

@DefaultHandler.register
class ScreenshotMessage:
    """Provides a message that is used for getting a screenshot of the InkyWHAT display"""
    MessageID = ID_SCREENSHOT

    def __init__(self, uid: int, output_path: str):
        """Constructor"""
        self.output_path = output_path
        self.uid = uid

    @classmethod
    def from_json(cls, message):
        """Creates a `ScreenshotMessage` from the provided JSON"""
        return cls(
            message["uid"],
            message["output_path"]
        )

    def to_json(self):
        """Returns a `ResponseMessage` that can be serialized to JSON"""
        return {
            "uid": self.uid,
            "output_path": self.output_path
        }

@DefaultHandler.register
class UpdateDisplayMessage:
    """Provides a message that is used for updating the InkyWHAT display"""
    MessageID = ID_UPDATE_DISPLAY

    def __init__(self,
                 artist_name: str,
                 album_name: str,
                 album_image_url: str,
                 device_name: str,
                 device_type: int,
                 duration_sec: int,
                 is_playing: bool,
                 is_shuffled: bool,
                 repeat_status: int,
                 track_name: str,
                 user_name: str,
                 user_image_url: str):
        """Constructor"""
        self.artist_name = artist_name
        self.album_name = album_name
        self.album_image_url = album_image_url
        self.device_name = device_name
        self.device_type = device_type
        self.duration_sec = duration_sec
        self.is_playing = is_playing
        self.is_shuffled = is_shuffled
        self.repeat_status = repeat_status
        self.track_name = track_name
        self.user_name = user_name
        self.user_image_url = user_image_url

    @classmethod
    def from_json(cls, message):
        """Creates an `UpdateDisplayMessage` from the provided JSON"""
        return cls(
            message["artist_name"],
            message["album_name"],
            message["album_image_url"],
            message["device_name"],
            message["device_type"],
            message["duration_sec"],
            message["is_playing"],
            message["is_shuffled"],
            message["repeat_status"],
            message["track_name"],
            message["user_name"],
            message["user_image_url"]
        )

    @classmethod
    def from_painter_options(cls, opts: PainterOptions):
        """Creates an `UpdateDisplayMessage` from the provided `PainterOptions`"""
        return cls(
            opts.artist_name,
            opts.album_name,
            opts.album_image_url,
            opts.device_name,
            opts.device_type,
            int(opts.duration.total_seconds()),
            opts.is_playing,
            opts.is_shuffled,
            opts.repeat_status,
            opts.track_name,
            opts.user_name,
            opts.user_image_url
        )

    def to_json(self):
        """Converts the message to a serializable JSON"""
        return {
            "artist_name": self.artist_name,
            "album_name": self.album_name,
            "album_image_url": self.album_image_url,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "duration_sec": self.duration_sec,
            "is_playing": self.is_playing,
            "is_shuffled": self.is_shuffled,
            "repeat_status": self.repeat_status,
            "track_name": self.track_name,
            "user_name": self.user_name,
            "user_image_url": self.user_image_url
        }

    def to_painter_options(self):
        """Returns the `PainterOptions` that was set for this message"""
        return PainterOptions(
            self.artist_name,
            self.album_name,
            self.album_image_url,
            self.device_name,
            self.device_type,
            timedelta(seconds=self.duration_sec),
            self.is_playing,
            self.is_shuffled,
            self.repeat_status,
            self.track_name,
            self.user_name,
            self.user_image_url
        )
