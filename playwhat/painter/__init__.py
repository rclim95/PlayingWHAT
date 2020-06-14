"""Initializes the `playwhat.painter` module"""
import logging
import os
from inky import InkyWHAT
from PIL import Image, ImageDraw, ImageFont
from playwhat.painter.types import PainterOptions, DeviceType, RepeatStatus
from playwhat.painter.paint import paint

LOGGER = logging.getLogger(__package__)

_current_options: PainterOptions = None

def display(options: PainterOptions) -> Image.Image:
    """
    Takes the image returned by `paint(options: PainterOptions)` and display it on the InkyWHAT
    display
    """
    global _current_options

    # Because it takes a long time to update the InkyWHAT, only update it _if_ we really have to
    if _current_options == options:
        LOGGER.warning("The options passed appears to be the same on screen, ignoring...")
        return
    else:
        _current_options = options

    # The display is up-side down, so rotate it. :)
    # TODO: Make this a config option.
    image = paint(options)
    image = image.rotate(180)

    inky_display = InkyWHAT("red")
    inky_display.set_border(InkyWHAT.WHITE)
    inky_display.set_image(image)
    inky_display.show()

def save_screenshot(output_path: str, uid: int):
    """
    Saves the screenshot of the InkyWHAT display to the speciifed `output_path`
    """
    if _current_options is None:
        # We haven't updated the screen, so we really don't know what the screen will look like.
        LOGGER.warning(
            "Can't save screenshot of InkyWHAT display: you must call display(PainterOptions) "
            "at least once before you can save a screenshot."
        )
        return

    try:
        screen = paint(_current_options)
        screen.putpalette((
            *(255, 255, 255),           # White
            *(0, 0, 0),                 # Black
            *(255, 0, 0),               # Red
            *((0, 0, 0) * 253)          # Remainder
        ))
        screen.save(output_path, format="PNG")

        os.chown(output_path, uid, -1)
    except Exception: # pylint: disable=broad-except
        LOGGER.exception("Failed to save screenshot to \"%s\"", output_path)
