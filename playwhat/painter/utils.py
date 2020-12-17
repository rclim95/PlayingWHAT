"""Provide utility functions for the `playwhat.painter` module"""

from datetime import timedelta
from hashlib import sha256
from io import BytesIO
import logging
import os
import re

from inky import InkyWHAT
from PIL import Image, ImageFont

import requests
from playwhat.painter.constants import PATH_IMAGE_CACHE, PATH_ASSET_FONT
from playwhat.painter.types import Dimension

# The logger for this module
LOGGER = logging.getLogger(__package__)

# A regex that can be used for determining if text is CJK. Obligatory "Thanks, StackOverflow":
# https://stackoverflow.com/a/30116125/3145126
_CJK_REGEX = re.compile(
    u"([\u3300-\u33ff\ufe30-\ufe4f\uf900-\ufaff\U0002f800-\U0002fa1f\u30a0-\u30ff\u2e80-\u2eff"
    u"\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f"
    u"\U0002b820-\U0002ceaf]+)")

class ImageCacheLibrary:
    """
    Provides a class that can be used for caching images to a place in the file system for
    later retrieval
    """

    def __init__(self, prefix: str):
        self._prefix = prefix

    def get_image(self, url: str):
        """
        Gets the image from the cache based on the provided `url`. If it doesn't exist, it'll be
        downloaded and then returned.
        """
        image_filepath = self._image_filepath(url)
        if not os.path.exists(image_filepath):
            # Download the file, since it doesn't exist.
            LOGGER.debug("\"%s\" does not exist, downloading...", image_filepath)
            return self._image_download(url)

        LOGGER.debug("\"%s\" already exists, returning cached copy...", image_filepath)
        return Image.open(image_filepath)

    def _image_filepath(self, url: str) -> str:
        image_filename = ImageCacheLibrary._image_filename(url)

        # To reduce the amount of files that needs to be loaded per directory, take the first two
        # hex digits and create a directory out of it, and then generate a file out of the rest.
        return os.path.join(self._prefix, image_filename[0:2], image_filename[2:])

    def _image_download(self, url: str) -> Image.Image:
        request = requests.get(url)
        image_filepath = self._image_filepath(url)

        # Create the directory to store our image if it doesn't exist
        image_directory = os.path.dirname(image_filepath)
        try:
            LOGGER.debug("Making directory \"%s\"", image_directory)
            os.makedirs(image_directory)
            LOGGER.debug("Directory \"%s\" created successfully", image_directory)
        except FileExistsError:
            LOGGER.debug("Directory \"%s\" already exists", image_directory)

        # Load up the image into PIL and then save it.
        with Image.open(BytesIO(request.content)) as image:  # type: Image.Image
            image.save(image_filepath, format="PNG")

            LOGGER.debug("\"%s\" saved successfully", image_filepath)
            return image

    @staticmethod
    def _image_filename(url: str) -> str:
        # Use the URL to generate the filename, so that we can lookup the image that we need to
        # return (given a URL) by its hash (rather than download the image and determine if we've
        # saved it already)
        return sha256(url.encode("utf-8")).hexdigest()

def create_image() -> Image.Image:
    """Creates a new, pallete-based `Image.Image` that can be placed on the Inky wHAT screen"""
    image = Image.new("P", (InkyWHAT.WIDTH, InkyWHAT.HEIGHT))
    image.putpalette((
        *(255, 255, 255),           # White
        *(0, 0, 0),                 # Black
        *(255, 0, 0),               # Red
        *((0, 0, 0) * 253)          # Remainder
    ))

    return image

def ellipsize_text(text: str, font: ImageFont.ImageFont, max_width: int) -> str:
    """
    Ellipsize the text if needed, accomodating for the `max_width` speciifed
    """
    # If the text is within max_width, just return the text.
    text_width, _ = font.getsize(text)
    if text_width <= max_width:
        return text

    # Otherwise, we'll need to do some ellipsizing.
    chars_end = 1
    while True:
        text_width, _ = font.getsize(text[:chars_end] + "...")
        if text_width < max_width:
            # Keep incrementing--we can fit more characters!
            chars_end += 1
            continue

        # All right, seems like we've reached our limit.
        return text[:chars_end - 1] + "..."

def get_font(text: str, size: int, light_variant: bool = False):
    """Gets the font to use depending on the provided text.

    If `text` contains Chinese, Japanese, or Korean characters, then a CJK font will be returned.
    Otherwise, the standard font will be used."""
    # Determine if the text contains characters that would require a CJK font to render
    # it properly (so that it isn't showing mojibake)
    if has_cjk_text(text):
        if light_variant:
            font_path = os.path.join(PATH_ASSET_FONT, "noto-sans-cjkjp-light.otf")
        else:
            font_path = os.path.join(PATH_ASSET_FONT, "noto-sans-cjkjp.otf")
    else:
        if light_variant:
            font_path = os.path.join(PATH_ASSET_FONT, "open-sans-light.ttf")
        else:
            font_path = os.path.join(PATH_ASSET_FONT, "open-sans.ttf")

    return ImageFont.truetype(font_path, size)

def get_image(url: str, resize_dimension: Dimension = None) -> Image.Image:
    """
    Gets an image from a URL that'll be quantizied (and optionally, resized) for the InkyWHAT
    display
    """
    # Gets an image
    cache = ImageCacheLibrary(prefix=PATH_IMAGE_CACHE)
    with cache.get_image(url) as image: # type: Image.Image
        return resize_and_quantize_to_what_display(image, resize_dimension)

def has_cjk_text(text: str):
    """
    Returns `True` if `text` contains Chinese, Japanese, or Korean text (and therefore, a CJK-
    compatible font should be used to display the text)
    """
    return _CJK_REGEX.search(text) is not None

def humanize_timedelta(delta: timedelta) -> str:
    """
    Returns a string that represents the `timedelta` that was passed in a more human-friendly manner
    """
    seconds = delta.total_seconds()
    if seconds < 60.0:
        return "{seconds:.0F}s ago".format(seconds=seconds)

    minutes = seconds / 60.0
    if minutes < 60.0:
        return "{minutes:.0F}m ago".format(minutes=minutes)

    hours = minutes / 60.0
    if hours < 24.0:
        return "{hours:.1F}h ago".format(hours=hours)

    days = hours / 24.0
    return "{days:.1F}d ago".format(days=days)

def resize_and_quantize_to_what_display(image: Image.Image,
                                        resize_dimension: Dimension = None) -> Image.Image:
    """
    Quantize, i.e., reduce the color depth of an image to a black, white, and red color palette
    suitable for the InkyWHAT display with the option to resize it to a specific dimension before
    hand.
    """
    with Image.new("P", (1, 1)) as palette:  # type: Image.Image
        palette.putpalette((
            *(255, 255, 255),           # White
            *(0, 0, 0),                 # Black
            *(255, 0, 0),               # Red
            *((0, 0, 0) * 253)          # Remainder
        ))

        # Resize the image, if specified. Note that we're using LANCZOS, a high-quality image
        # resizing algorithm.
        if resize_dimension is not None:
            image = image.resize(resize_dimension, resample=Image.LANCZOS)

        return image.convert("RGB").quantize(palette=palette)

def wrap_and_ellipsize_text(text: str,
                            font: ImageFont.ImageFont,
                            max_width: int,
                            max_lines: int) -> str:
    """
    Tries to force `text` to fit within the specified `max_width`, up to `max_lines`. If it does
    not fit, an attempt will be made to wrap the text (up to `max_lines`). If the text exceeds
    `max_lines`, then the text will be ellipsized.
    """
    # Strip out any whitespaces
    text = text.strip()

    # Split up text by word boundaries, i.e., by spaces. Note that to prevent weird issues
    # with text that may have double spaces (which will result an empty word token), we'll
    # filter it out.
    words = list(filter(lambda word: word.strip() != "", text.split()))

    current_line = 1
    current_line_str = ""
    output = ""
    for index, word in enumerate(words):
        # Will adding this word exceed our max_width?
        next_output = current_line_str + word
        output_width, _ = font.getsize(next_output)

        if output_width > max_width:
            # Can we insert a line break?
            if current_line == max_lines:
                # Nope, this means that we're going to need to truncate this word. To make
                # sure we're ellipsizing correctly, assume that we're adding the rest of the song
                # title to the current line.
                current_line_str += " ".join(words[index:])
                output += ellipsize_text(current_line_str, font, max_width)

                return output

            # We can insert a line break here. Do that, and move our next word there.
            output += current_line_str + "\n"
            current_line_str = word + " "
            current_line += 1
        else:
            # We're still good. Append it. :)
            current_line_str += word + " "

    # If we've reached this far, that means we were able to fit all the words of the track.
    # Depending on what output and current_line_str is, we may need to do some ellipsizing here.
    if len(output) == 0 and len(current_line_str) > 0:
        # That means by the time we were enumerating through all words, we were able fit every word
        # of the track to our current_line_str without appending to the output. Return
        # current_line_str in that case, ellipsizing as needed.
        return ellipsize_text(current_line_str.strip(), font, max_width)
    else:
        # Otherwise, we had some output and we were able to append the remaining words to
        # current_line_str without exceeding the max_lines. In that case, append the output and the
        # current_line_str together.
        return output + ellipsize_text(current_line_str.strip(), font, max_width)
