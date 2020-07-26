"""Provide functions that's responsible for doing the actual painting/drawing on the display"""

import re

from inky import InkyWHAT
from PIL import Image, ImageDraw, ImageFont

from playwhat.painter import utils
from playwhat.painter.constants import *
from playwhat.painter.types import *

# Obligatory "Thanks, StackOverflow": https://stackoverflow.com/a/30116125/3145126
_CJK_REGEX = re.compile(u"([\u3300-\u33ff\ufe30-\ufe4f\uf900-\ufaff\U0002f800-\U0002fa1f\u30a0-\u30ff\u2e80-\u2eff\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f\U0002b820-\U0002ceaf]+)")

def paint(options: PainterOptions) -> Image.Image:
    """
    Paints the "Now Playing" screen based off the options passed to the `options` parameter and
    returns a `PIL.Image` that can be shown on the InkyWHAT display
    """
    image = Image.new("P", (InkyWHAT.WIDTH, InkyWHAT.HEIGHT))
    image.putpalette((
        *(255, 255, 255),           # White
        *(0, 0, 0),                 # Black
        *(255, 0, 0),               # Red
        *((0, 0, 0) * 253)          # Remainder
    ))
    draw = ImageDraw.Draw(image)
    _paint_header(image, draw, options)
    _paint_content(image, draw, options)
    _paint_footer(image, draw, options)

    return image

def paint_not_playing() -> Image.Image:
    """
    Paints the "Not Playing" screen and returns a `PIL.Image` that can be shown on the InkyWHAT
    display
    """
    image = Image.new("P", (InkyWHAT.WIDTH, InkyWHAT.HEIGHT))
    image.putpalette((
        *(255, 255, 255),           # White
        *(0, 0, 0),                 # Black
        *(255, 0, 0),               # Red
        *((0, 0, 0) * 253)          # Remainder
    ))
    draw = ImageDraw.Draw(image)

    # Draw the music icon
    with Image.open(os.path.join(PATH_ASSET_IMAGE, "icon-music.png")) as music:
        music_width, music_height = music.width, music.height
        image.paste(music, ((image.width - music_width) // 2, PADDING))

    # Figure out how to draw the heading text, which should appear beneath the music icon, also
    # centered.
    heading_text = "Nothing's Playing\nRight Now"
    heading_font = ImageFont.truetype(
        os.path.join(PATH_ASSET_FONT, "open-sans.ttf"),
        size=NOT_PLAYING_HEADING_POINT_SIZE)
    heading_width, heading_height = heading_font.getsize_multiline(heading_text)
    heading_x = (image.width - heading_width) // 2
    heading_y = PADDING + music_height + NOT_PLAYING_ICON_SPACING

    # Now draw the heading text
    draw.multiline_text(
        (heading_x, heading_y), heading_text,
        align="center", font=heading_font, fill=InkyWHAT.RED)

    # Figure out how to draw the context text, which should appear underneath the heading text,
    # also centered.
    content_text = "Play some music on Spotify, and we'll\nshow what's playing on here. :)"
    content_font = ImageFont.truetype(
        os.path.join(PATH_ASSET_FONT, "open-sans.ttf"),
        size=NOT_PLAYING_CONTENT_POINT_SIZE)
    content_width, _ = content_font.getsize_multiline(content_text)
    content_x = (image.width - content_width) // 2
    content_y = PADDING + music_height + NOT_PLAYING_ICON_SPACING + heading_height + \
        NOT_PLAYING_HEADING_SPACING

    # Now draw the content text
    draw.multiline_text(
        (content_x, content_y), content_text,
        align="center", font=content_font, fill=InkyWHAT.RED
    )

    return image

def _paint_header(image: Image.Image, draw: ImageDraw.ImageDraw, options: PainterOptions):
    # Draw the Spotify logo
    with Image.open(os.path.join(PATH_ASSET_IMAGE, "logo-spotify.png")) as logo:
        logo_height = logo.height
        logo_width = logo.width
        image.paste(logo, (PADDING, PADDING))

    # Determine if the user is playing now or has stopped playing and then draw the text
    if options.is_playing:
        heading_text = "• Now Playing"
    else:
        heading_text = "• Was Playing"

    # Measure the text and figure out how to draw it
    font = ImageFont.truetype(
        os.path.join(PATH_ASSET_FONT, "open-sans-light.ttf"),
        size=HEADING_POINT_SIZE)
    _, heading_height = font.getsize(heading_text)

    # Ensure that the font aligns within the middle of the logo's height
    heading_x = PADDING + logo_width + HEADING_LOGO_TEXT_SPACING
    heading_y = PADDING + ((logo_height - heading_height) // 2) - 2

    # Now draw it.
    draw.text((heading_x, heading_y), heading_text, font=font, fill=InkyWHAT.BLACK)

    # Determine the shuffle and repeat state and figure out which icon do we want to draw
    if options.is_shuffled:
        shuffle_icon_path = os.path.join(PATH_ASSET_IMAGE, "icon-shuffle.png")
    else:
        shuffle_icon_path = os.path.join(PATH_ASSET_IMAGE, "icon-shuffle-disabled.png")

    # Draw the shuffle icon first, at the very right of the screen
    with Image.open(shuffle_icon_path) as shuffle:  # type: Image.Image
        shuffle_x = InkyWHAT.WIDTH - PADDING - shuffle.width
        shuffle_y = PADDING + ((logo_height - shuffle.height) // 2)
        image.paste(shuffle, (shuffle_x, shuffle_y))

    if options.repeat_status == RepeatStatus.OFF:
        repeat_icon_path = os.path.join(PATH_ASSET_IMAGE, "icon-repeat-disabled.png")
    elif options.repeat_status == RepeatStatus.SINGLE:
        repeat_icon_path = os.path.join(PATH_ASSET_IMAGE, "icon-repeat-one.png")
    else:
        repeat_icon_path = os.path.join(PATH_ASSET_IMAGE, "icon-repeat.png")

    # Draw the repeat icon afterwards, before the shuffle icon
    with Image.open(repeat_icon_path) as repeat:  # type: Image.Image
        repeat_x = shuffle_x - HEADING_REPEAT_SHUFFLE_SPACING - repeat.width
        repeat_y = shuffle_y
        image.paste(repeat, (repeat_x, repeat_y))

    # Determine the like state and figure out what icon do we need to draw
    if options.is_liked:
        like_icon_path = os.path.join(PATH_ASSET_IMAGE, "icon-heart.png")
    else:
        like_icon_path = os.path.join(PATH_ASSET_IMAGE, "icon-heart-outline.png")

    # Finally, draw the heart icon afterwards, before the shuffle icon
    with Image.open(like_icon_path) as like: # type: Image.image
        like_x = repeat_x - HEADING_REPEAT_SHUFFLE_SPACING - like.width
        like_y = shuffle_y
        image.paste(like, (like_x, like_y))

def _paint_content(image: Image.Image, draw: ImageDraw.ImageDraw, options: PainterOptions):
    # Figure out where we should start drawing the album art (and title). We're going to try
    # to center it on the screen of the InkyWHAT.
    content_y = None
    if CONTENT_START_Y is None:
        content_y = (image.height - CONTENT_ALBUM_DIMENSIONS[1]) // 2
    else:
        content_y = CONTENT_START_Y

    # Draw the album part. Note that if no album art is provided, we'll provide a generic one.
    if options.album_image_url is None:
        album_art = Image.open(os.path.join(PATH_ASSET_IMAGE, "album-generic.png"))
    else:
        album_art = utils.get_image(options.album_image_url,
                                    resize_dimension=CONTENT_ALBUM_DIMENSIONS)

    with album_art:
        album_art_width = album_art.width
        album_art_height = album_art.height
        album_art_x = PADDING
        album_art_y = content_y
        image.paste(album_art, (album_art_x, album_art_y))

    title_font = _get_font(options.track_name, CONTENT_TRACK_POINT_SIZE)

    # Now figure out how to write the track title (wrapping and ellipsizing as needed)
    max_width = image.width - ((PADDING * 2) + album_art_width + CONTENT_ALBUM_ART_INFO_SPACING)
    title_wrapped = utils.wrap_and_ellipsize_text(options.track_name, title_font,
                                                  max_width=max_width,
                                                  max_lines=2)
    title_x = PADDING + album_art_width + CONTENT_ALBUM_ART_INFO_SPACING
    title_y = content_y
    draw.multiline_text((title_x, title_y), title_wrapped, fill=InkyWHAT.RED, font=title_font)

    info_font = ImageFont.truetype(
        os.path.join(PATH_ASSET_FONT, "open-sans.ttf"),
        size=CONTENT_INFO_POINT_SIZE
    )

    # Draw the song duration first. Note that we're starting from the bottom, and then drawing up.
    album_bottom_y = album_art_y + album_art_height
    duration_secs = int(options.duration.total_seconds())
    duration_text = "{mins:d}:{secs:02d}".format(mins=duration_secs // 60, secs=duration_secs % 60)
    info_height = _paint_content_info(
        image=image,
        draw=draw,
        font=info_font,
        info_x=title_x,
        info_bottom_y=album_bottom_y,
        icon_path=os.path.join(PATH_ASSET_IMAGE, "icon-duration.png"),
        text=duration_text,
        max_width=max_width
    )

    # Draw the artist next.
    info_height += _paint_content_info(
        image=image,
        draw=draw,
        font=_get_font(options.artist_name, CONTENT_INFO_POINT_SIZE),
        info_x=title_x,
        info_bottom_y=album_bottom_y - info_height - CONTENT_INFO_LINE_SPACING,
        icon_path=os.path.join(PATH_ASSET_IMAGE, "icon-artist.png"),
        text=options.artist_name,
        max_width=max_width
    )
    info_height += CONTENT_INFO_LINE_SPACING

    # Finally, draw the album title.
    _paint_content_info(
        image=image,
        draw=draw,
        font=_get_font(options.album_name, CONTENT_INFO_POINT_SIZE),
        info_x=title_x,
        info_bottom_y=album_bottom_y - info_height,
        icon_path=os.path.join(PATH_ASSET_IMAGE, "icon-album.png"),
        text=options.album_name,
        max_width=max_width
    )

def _paint_content_info(image: Image.Image, draw: ImageDraw.ImageDraw, font: ImageFont.ImageFont,
                        info_x: int, info_bottom_y: int,
                        icon_path: str, text: str, max_width=int):
    # Draw the icon
    with Image.open(icon_path) as icon:
        icon_width = icon.width
        icon_height = icon.height
        image.paste(icon, (info_x, info_bottom_y - icon_height))

    # Draw the text
    text_x = info_x + icon_width + CONTENT_INFO_ICON_SPACING
    text_y = info_bottom_y - icon_height
    draw.text(
        (text_x, text_y),
        utils.ellipsize_text(text, font, max_width - icon_width - CONTENT_INFO_ICON_SPACING),
        font=font, fill=InkyWHAT.BLACK)

    # Return the height of the icon (so that we know where to draw the next info)
    return icon_height

def _paint_footer(image: Image.Image, draw: ImageDraw.ImageDraw, options: PainterOptions):
    # Draw the user's icon
    with utils.get_image(options.user_image_url, (30, 30)) as avatar_image:
        avatar_image_width = avatar_image.width
        avatar_image_height = avatar_image.height
        avatar_image_x = PADDING
        avatar_image_y = image.height - PADDING - avatar_image_height
        image.paste(avatar_image, (avatar_image_x, avatar_image_y))

    font = ImageFont.truetype(
        os.path.join(PATH_ASSET_FONT, "open-sans-light.ttf"),
        size=FOOTER_POINT_SIZE)

    # Draw the user's name
    _, name_text_height = draw.textsize(options.user_name, font)
    name_max_width = ((image.width - (PADDING * 2)) // 2) - \
        avatar_image_width - FOOTER_ICON_NAME_SPACING - \
        (FOOTER_USER_DEVICE_SPACING // 2)
    name_x = avatar_image_x + avatar_image_width + FOOTER_ICON_NAME_SPACING
    name_y = avatar_image_y + ((avatar_image_height - name_text_height) // 2) - 2
    draw.text(
        (name_x, name_y),
        utils.ellipsize_text(options.user_name, font, name_max_width),
        fill=InkyWHAT.BLACK, font=font)

    # Figure out which icon to draw and draw it
    if options.device_type == DeviceType.COMPUTER:
        device_icon_path = os.path.join(PATH_ASSET_IMAGE, "icon-computer.png")
    elif options.device_type == DeviceType.PHONE:
        device_icon_path = os.path.join(PATH_ASSET_IMAGE, "icon-phone.png")
    elif options.device_type == DeviceType.SPEAKER:
        device_icon_path = os.path.join(PATH_ASSET_IMAGE, "icon-speaker.png")
    elif options.device_type == DeviceType.TV:
        device_icon_path = os.path.join(PATH_ASSET_IMAGE, "icon-tv.png")
    else:
        device_icon_path = os.path.join(PATH_ASSET_IMAGE, "icon-other.png")

    with Image.open(device_icon_path) as device_icon:  # type: Image.Image
        device_width = device_icon.width
        device_height = device_icon.height

        # Measure out the device's name so we know how much space we'll need to allocate. The device
        # name can take up to half the image's width (while including enough space for the icon)
        device_name_max_width = ((image.width - (PADDING * 2)) // 2) - \
            device_width - FOOTER_ICON_NAME_SPACING - \
            (FOOTER_USER_DEVICE_SPACING // 2)
        device_name = utils.ellipsize_text(options.device_name, font, device_name_max_width)
        device_name_width, device_name_height = draw.textsize(device_name, font)

        device_x = image.width - PADDING - device_name_width - \
            FOOTER_ICON_NAME_SPACING - device_width
        device_y = avatar_image_y + ((avatar_image_height - device_height) // 2)

        # Now that we've done all of our management, it's time to draw it.
        image.paste(device_icon, (device_x, device_y))

        # Draw the text
        draw.text(
            (device_x + + device_width + FOOTER_ICON_NAME_SPACING,
             device_y + ((device_height - device_name_height) // 2) - 2),
            device_name, font=font, fill=InkyWHAT.BLACK)

def _get_font(text: str, size: int, light_variant: bool = False):
    # Determine if the text contains characters that would require a CJK font to render
    # it properly (so that it isn't showing mojibake)
    if _CJK_REGEX.search(text) is not None:
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
