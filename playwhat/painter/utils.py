"""Provide utility functions for the `playwhat.painter` module"""

from hashlib import sha256
from io import BytesIO
import logging
import os
from PIL import Image, ImageFont
import requests
from playwhat.painter.constants import PATH_IMAGE_CACHE
from playwhat.painter.types import Dimension

# The logger for this module
LOGGER = logging.getLogger(__package__)

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

def get_image(url: str, resize_dimension: Dimension = None) -> Image.Image:
    """
    Gets an image from a URL that'll be quantizied (and optionally, resized) for the InkyWHAT
    display
    """
    # Gets an image
    cache = ImageCacheLibrary(prefix=PATH_IMAGE_CACHE)
    with cache.get_image(url) as image: # type: Image.Image
        return resize_and_quantize_to_what_display(image, resize_dimension)

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

def ellipsize_text(text: str, font: ImageFont.ImageFont, max_width: int) -> str:
    """
    Ellipsize the text if needed, accomodating for the `max_width` speciifed
    """
    # If the text is within max_width, just return the text.
    text_width, _ = font.getsize(text)
    if text_width <= max_width:
        return text

    # Otherwise, we'll need to do some ellipsizing.
    ellipsis_width, _ = font.getsize("…")
    chars_to_subtract = 1
    while True:
        text_width, _ = font.getsize(text[:-chars_to_subtract])
        if text_width + ellipsis_width < max_width:
            # We're good to go
            return text[:-chars_to_subtract] + "…"

        # Nope, we need to keep subtracting.
        chars_to_subtract += 1

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

    result = ""
    last_space = 0
    line_count = 1      # The number of lines we've written so far
    line_start = 0      # The character in text where the line starts.
    line_width = 0      # The width of all characters in the current line
    for index, char in enumerate(text):
        # Keep track of the last whitespace that we have found in the text so we know
        # where to insert a line break later.
        if char.isspace():
            last_space = index

        # Measure the width of the character
        char_width, _ = font.getsize(char)

        # Will we have enough space to render this character?
        if max_width - line_width - char_width > 0:
            # Cool. Add it to the total line width that we've recorded so far.
            line_width += char_width
        else:
            # If we didn't come across a space, then most likely, this is a super long word we're
            # working with. In that case, let last_space be the current index.
            if last_space == 0:
                last_space = index

            # Nope, we're going to need to introduce a line break somewhere. Capture the line that
            # we want to flush.
            line = text[line_start:last_space]

            # Can we write a new line? That is, make sure we haven't reached our maximum line.
            if line_count == max_lines:
                # We've reached our maximum line. Ellipsize our last line.
                return result + ellipsize_text(line, font, max_width)

            # We haven't reached our maximum line. Append a new line and continue.
            result += line + "\n"

            # Now we need to write the characters starting from last_space up to index and reset
            # line_width to accomodate for the remaining text we've just inserted in the new line
            # we've created.
            remaining = text[last_space + 1:index]
            result += remaining
            line_width, _ = font.getsize(remaining)

            # The current character we're processing at index is now our new "line_start" index.
            line_start = index
            line_count += 1

    # If we've reached this part, that means we were able to fit everything. In that case,
    # flush out everyhing that remains in our buffer.
    result += text[line_start:]
    return result
