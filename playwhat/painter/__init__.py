"""Initializes the `playwhat.painter` module"""
import logging
import os
from typing import List
from inky import InkyWHAT
from PIL import Image, ImageDraw, ImageFont
import playwhat
from playwhat.painter.types import PainterOptions, RecentTrackOptions, \
    RecentTrack, \
    DeviceType, \
    RepeatStatus
import playwhat.painter.screens as s

LOGGER = logging.getLogger(__package__)

_current_options: PainterOptions = None
_current_recent_tracks: RecentTrackOptions = None

def display(options: PainterOptions, force=False) -> Image.Image:
    """
    Takes the image returned by `paint(options: PainterOptions)` and display it on the InkyWHAT
    display
    """
    global _current_options, _current_recent_tracks # pylint: disable=invalid-name,global-statement

    # Because it takes a long time to update the InkyWHAT, only update it _if_ we really have to
    if not force and _current_options == options:
        LOGGER.warning("The options passed appears to be the same on screen, ignoring...")
        return

    _current_options = options

    # Reset the recent tracks to None, since we're playing something.
    _current_recent_tracks = None

    image_rotate_degrees = os.getenv(playwhat.ENV_ROTATE_IMAGE, "180")
    image = s.now_playing.create(options)
    image = image.rotate(int(image_rotate_degrees))

    inky_display = InkyWHAT("red")
    inky_display.set_border(InkyWHAT.WHITE)
    inky_display.set_image(image)
    inky_display.show()

def display_not_playing(force=False) -> Image.Image:
    """
    Shows the "Not Playing" screen on the InkyWHAT display
    """
    global _current_options, _current_recent_tracks # pylint: disable=invalid-name,global-statement

    # Because it takes a long time to update the InkyWHAT, only update it _if_ we really have to
    if not force and _current_options is None:
        LOGGER.warning("The \"Not Playing\" screen is already shown, ignoring...")
        return

    # We're not playing anything, so set _current_options to None
    _current_options = None

    # We're not displaying the list of recent tracks, so reset that too.
    _current_recent_tracks = None

    image_rotate_degrees = os.getenv(playwhat.ENV_ROTATE_IMAGE, "180")
    image = s.not_playing.create()
    image = image.rotate(int(image_rotate_degrees))

    inky_display = InkyWHAT("red")
    inky_display.set_border(InkyWHAT.WHITE)
    inky_display.set_image(image)
    inky_display.show()

def display_recently_played(options: RecentTrackOptions, force=False) -> Image.Image:
    """
    Shows the "Recently Played" screen on the InkyWHAT display
    """
    global _current_options, _current_recent_tracks # pylint: disable=invalid-name,global-statement

    # Because it takes a long time to update the InkyWHAT, only update it _if_ we really have to.
    # Note that we're not going to be comparing _current_recent_tracks and options--instead, we're
    # going to compare the track list (since that's where the "interesting" differences lie).
    if not force and \
       _current_recent_tracks is not None and \
       _current_recent_tracks.tracks == options.tracks:
        LOGGER.warning("The list of recent tracks appear to be same on screen, ignoring...")
        return

    # We're not playing anything, so reset _current_options to None
    _current_options = None

    # Store the list of recent tracks that we got (don't store the options, because we don't care
    # about the "timestamp" property--only whether the list of recent tracks have changed)
    _current_recent_tracks = options

    image_rotate_degrees = os.getenv(playwhat.ENV_ROTATE_IMAGE, "180")
    image = s.recently_played.create(options)
    image = image.rotate(int(image_rotate_degrees))

    inky_display = InkyWHAT("red")
    inky_display.set_border(InkyWHAT.WHITE)
    inky_display.set_image(image)
    inky_display.show()

def save_screenshot(output_path: str, uid: int):
    """
    Saves the screenshot of the InkyWHAT display to the specified `output_path`
    """
    try:
        if _current_options is None:
            # Are we supposed to paint the "Recently Played" list?
            if _current_recent_tracks is None:
                screen = s.not_playing.create()
            else:
                screen = s.recently_played.create(_current_recent_tracks)
        else:
            screen = s.now_playing.create(_current_options)

        screen.save(output_path, format="PNG")

        os.chown(output_path, uid, -1)
    except Exception: # pylint: disable=broad-except
        LOGGER.exception("Failed to save screenshot to \"%s\"", output_path)
