"""Initializes the `playwhat.painter` module"""

import os
from inky import InkyWHAT
from PIL import Image, ImageDraw, ImageFont
from playwhat.painter.types import PainterOptions, DeviceType, RepeatStatus
from playwhat.painter.paint import paint

def display(options: PainterOptions) -> Image.Image:
    """
    Takes the image returned by `paint(options: PainterOptions)` and display it on the InkyWHAT
    display
    """
    inky_display = InkyWHAT("red")
    inky_display.set_border(InkyWHAT.WHITE)
    inky_display.set_image(paint(options))
    inky_display.show()
