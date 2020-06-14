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
