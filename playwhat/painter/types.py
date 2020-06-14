"""Provides access to types that's used by the painter"""

import typing
from dataclasses import dataclass
from datetime import timedelta
from enum import IntEnum

# Represents a dimension in the form (int, int)
Dimension = typing.Tuple[int, int]

class DeviceType(IntEnum):
    """
    Defines the available device types that the player can stream their track to
    """
    COMPUTER = 0
    PHONE = 1
    SPEAKER = 2
    TV = 3
    OTHER = 4

    def __str__(self) -> str:
        """Gets a human-readable string of the enum"""
        return self.name

    @staticmethod
    def from_string(string: str):
        """Gets an enum value from a string"""
        try:
            return DeviceType[string]
        except KeyError as error:
            raise ValueError from error

    @staticmethod
    def from_api(string: str):
        """Gets an enum value from a string that was returned from Spotify's API"""
        if string == "Computer":
            return DeviceType.COMPUTER
        elif string == "Smartphone":
            return DeviceType.PHONE
        elif string == "TV":
            return DeviceType.TV
        elif string == "Speaker":
            return DeviceType.SPEAKER
        else:
            return DeviceType.OTHER

class RepeatStatus(IntEnum):
    """
    Defines the available repeat status
    """
    OFF = 0         # Repeat is currently not enabled.
    SINGLE = 1      # Repeat one track only.
    ALL = 2         # Repeat all songs in the playlist or album.

    def __str__(self):
        """Gets a human-readable string of the enum"""
        return self.name

    @staticmethod
    def from_string(string: str):
        """Gets an enum value from a string"""
        try:
            return RepeatStatus[string]
        except KeyError as error:
            raise ValueError from error

    @staticmethod
    def from_api(string: str):
        """Gets an enum value from a string that was returned from Spotify's API"""
        if string == "track":
            return RepeatStatus.SINGLE
        elif string == "context":
            return RepeatStatus.ALL
        else:
            return RepeatStatus.OFF

@dataclass
class PainterOptions:
    """
    Defines the available options that can be passed to the painter so it'll know what to paint
    """
    artist_name: str
    album_name: str
    album_image_url: str
    device_name: str
    device_type: DeviceType
    duration: timedelta
    is_playing: bool
    is_shuffled: bool
    repeat_status: RepeatStatus
    track_name: str
    user_name: str
    user_image_url: str
