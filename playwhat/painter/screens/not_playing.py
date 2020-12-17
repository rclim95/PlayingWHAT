"""Provide functions for creating an image of the **Not Playing** screen"""
from inky import InkyWHAT
from PIL import Image, ImageDraw, ImageFont

from playwhat.painter import utils
from playwhat.painter.constants import *
from playwhat.painter.types import *

def create() -> Image.Image:
    """
    Creates an image of the the "Not Playing" screen and returns a `PIL.Image` that can be shown
    on the InkyWHAT display
    """
    image = utils.create_image()
    draw = ImageDraw.Draw(image)

    max_width = image.width - (PADDING * 2)

    # Get the music icon that'll be shown above the header
    music_icon = Image.open(os.path.join(PATH_ASSET_IMAGE, "icon-music.png"))

    # Layout out heading
    heading_font = ImageFont.truetype(
        os.path.join(PATH_ASSET_FONT, "open-sans.ttf"),
        size=NOT_PLAYING_HEADING_POINT_SIZE)
    heading_text = utils.wrap_and_ellipsize_text(
        text="There Is Nothing Playing",
        font=heading_font,
        max_width=max_width,
        max_lines=2)
    heading_text_width, heading_text_height = heading_font.getsize_multiline(heading_text)

    # Layout our content
    content_font = ImageFont.truetype(
        os.path.join(PATH_ASSET_FONT, "open-sans.ttf"),
        size=NOT_PLAYING_CONTENT_POINT_SIZE)
    content_text = utils.wrap_and_ellipsize_text(
        text="Play some music on Spotify, and we will show you what is playing on here. :)",
        font=content_font,
        max_width=max_width,
        max_lines=2)
    content_text_width, content_text_height = content_font.getsize_multiline(content_text)

    # Figure out where the y-start of our music icon should be drawn. This is dependent on
    #   1) The music icon's height
    #   2) The text height of the heading
    #   3) The text height of the content
    #   4) The padding between the music icon, heading, and content
    y_start = (image.height - (music_icon.height + \
              NOT_PLAYING_ICON_SPACING + \
              heading_text_height + \
              NOT_PLAYING_HEADING_SPACING + \
              content_text_height)) // 2

    # Subtracting 10 from the initial y_start so that it's visually centered (this doesn't make it
    # vertically centered, but at least it looks like it's centered, psychologically-speaking)
    # See: https://photo.stackexchange.com/a/21452
    y_start -= 10

    # Now start drawing the music icon
    music_x = (image.width - music_icon.width) // 2
    music_y = y_start
    image.paste(music_icon, (music_x, music_y))

    # Then start drawing the header
    heading_x = (image.width - heading_text_width) // 2
    heading_y = music_y + music_icon.height + NOT_PLAYING_ICON_SPACING
    draw.multiline_text((heading_x, heading_y), heading_text,
                        font=heading_font,
                        align="center",
                        fill=InkyWHAT.RED)

    # And finally, the content
    content_x = (image.width - content_text_width) // 2
    content_y = heading_y + heading_text_height + NOT_PLAYING_HEADING_SPACING
    draw.multiline_text((content_x, content_y), content_text,
                        font=content_font,
                        align="center",
                        fill=InkyWHAT.RED)

    return image
