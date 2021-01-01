"""Provide functions for creating an image of the **Recently Played** screen"""
from inky import InkyWHAT
from PIL import Image, ImageDraw, ImageFont

from playwhat.painter import utils
from playwhat.painter.constants import *
from playwhat.painter.types import *

def create(options: RecentTrackOptions) -> Image.Image:
    """
    Creates an image of the "Recently Played" screen based off the provided options and returns a
    `PIL.Image` that can be shown on the InkyWHAT display
    """
    image = utils.create_image()
    draw = ImageDraw.Draw(image)
    _paint_header(image, draw)
    _paint_list(image, draw, options)
    _paint_footer(image, draw, options)

    return image


def _paint_header(image: Image.Image, draw: ImageDraw.ImageDraw):
     # Draw the Spotify logo
    with Image.open(os.path.join(PATH_ASSET_IMAGE, "logo-spotify.png")) as logo:
        logo_height = logo.height
        logo_width = logo.width
        image.paste(logo, (PADDING, PADDING))

    heading_text = "• Recently Played"

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

def _paint_list(image: Image.Image, draw: ImageDraw.ImageDraw, options: RecentTrackOptions):
    # Estimate the height of the content. We need to take into consideration:
    # - The spacing between the header and content of the track table
    # - The number of tracks that's going to be listed
    # - The spacing between the tracks listed
    track_count = len(options.tracks)
    content_height = RECENTLY_PLAYED_HEADING_POINT_SIZE + \
        RECENTLY_PLAYED_CELL_SPACING + \
        (RECENTLY_PLAYED_CONTENT_POINT_SIZE * track_count) + \
        (RECENTLY_PLAYED_ROW_SPACING * (track_count - 1))

    # Figure out where we should start drawing the recently played tracks list. We're going to try
    # to center it on the screen of the InkyWHAT.
    content_y = None
    if CONTENT_START_Y is None:
        content_y = (image.height - content_height - (PADDING * 2)) // 2
    else:
        content_y = CONTENT_START_Y

    # Measure out our header. The first column (track name) should take up three-fifths of the
    # screen. The second column (artist) should take up two-fifths of the screen's width.
    track_name_column_x = PADDING
    track_name_column_width = (image.width - (PADDING * 2)) * (3 / 5)
    artist_name_column_x = track_name_column_x + track_name_column_width + \
        RECENTLY_PLAYED_CELL_SPACING
    artist_name_column_width = (image.width - (PADDING * 2)) * (2 / 5)

    # Get the header font that we want to use to draw our table headers
    header_font = ImageFont.truetype(
        os.path.join(PATH_ASSET_FONT, "open-sans.ttf"),
        size=RECENTLY_PLAYED_HEADING_POINT_SIZE)

    # Measure out the header font so we know where we need to draw our table line. Note that we
    # used "Played", since this header text will be the tallest (due to the "y").
    # pylint: disable=unused-variable # Reason: header_font_weight must be declared.
    header_font_width, header_font_height = draw.textsize("Played", font=header_font)
    header_line_y = content_y + header_font_height + (RECENTLY_PLAYED_CELL_SPACING // 2)

    # Draw out our header (using the above measurements to figure out *where* to place the header)
    draw.text((track_name_column_x, content_y), text="Track", fill=InkyWHAT.RED, font=header_font)
    draw.text((artist_name_column_x, content_y), text="Artist", fill=InkyWHAT.RED, font=header_font)
    draw.line(((PADDING, header_line_y), (image.width - PADDING, header_line_y)),
        fill=InkyWHAT.RED,
        width=1)

    # Get the font for writing the "Played Ago" text
    played_ago_font = ImageFont.truetype(
        os.path.join(PATH_ASSET_FONT, "open-sans.ttf"),
        size=RECENTLY_PLAYED_CONTENT_POINT_SIZE
    )

    # Now draw our list of tracks that was recently played
    line_y = header_line_y + (RECENTLY_PLAYED_CELL_SPACING // 2)
    for track in options.tracks:
        # Figure out which font we need to get (in case we're dealing with a track name who's CJK)
        content_font = utils.get_font(
            text=track.track_name,
            size=RECENTLY_PLAYED_CONTENT_POINT_SIZE)

        # Figure out how much space to allocate to the track's name. It'll either be
        # the entire column width (if this track was played once) or a part of it (if this track
        # was played multiple time consecutively)
        if track.times_played > 1:
            # This track got played multiple time. Figure out how much space to allocate for
            # writing the (× <Times Played>) part of the title.
            times_played = "(× {count})".format(count=track.times_played)
            times_played_width, times_played_height = content_font.getsize(times_played)
            track_name_max_width = track_name_column_width - times_played_width

            # Draw the times_played part at the very end of the "Track" column
            draw.text((PADDING + track_name_column_width - times_played_width, line_y),
                text=times_played,
                fill=InkyWHAT.RED,
                font=content_font)
        else:
            track_name_max_width = track_name_column_width

        # Draw the track's name first
        track_name = utils.ellipsize_text(
            track.track_name,
            font=content_font,
            max_width=track_name_max_width)
        draw.text((PADDING, line_y),
            text=track_name,
            fill=InkyWHAT.BLACK,
            font=content_font)

        # Then draw the artist's name next
        content_font = utils.get_font(
            text=track.artist_name,
            size=RECENTLY_PLAYED_CONTENT_POINT_SIZE)
        artist_name = utils.ellipsize_text(
            track.artist_name,
            font=content_font,
            max_width=artist_name_column_width)
        draw.text((artist_name_column_x, line_y),
            text=artist_name,
            fill=InkyWHAT.BLACK,
            font=content_font)

        # Adjust line_y for the next line
        line_y += RECENTLY_PLAYED_CONTENT_POINT_SIZE + RECENTLY_PLAYED_ROW_SPACING

def _paint_footer(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    options: RecentTrackOptions):
    # Draw the user's icon
    with utils.get_image(options.user_image_url, (40, 40)) as avatar_image:
        avatar_image_width = avatar_image.width
        avatar_image_height = avatar_image.height
        avatar_image_x = PADDING
        avatar_image_y = image.height - PADDING - avatar_image_height

        # Create a circular image mask so that we can apply it to the user's avatar
        circle_mask = Image.new(mode="1", size=(avatar_image_width, avatar_image_height))
        circle_mask_draw = ImageDraw.Draw(circle_mask)
        circle_mask_draw.ellipse([(0, 0), (circle_mask.width, circle_mask.height)], fill=1)

        image.paste(avatar_image, (avatar_image_x, avatar_image_y), mask=circle_mask)

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

    # Draw the time the screen was last updated
    recent_icon_path = os.path.join(PATH_ASSET_IMAGE, "icon-recent.png")
    with Image.open(recent_icon_path) as recent_icon:  # type: Image.Image
        recent_icon_width = recent_icon.width
        recent_icon_height = recent_icon.height

        # Measure out the device's name so we know how much space we'll need to allocate. The device
        # name can take up to half the image's width (while including enough space for the icon)
        recent_timestamp_max_width = ((image.width - (PADDING * 2)) // 2) - \
            recent_icon_width - FOOTER_ICON_NAME_SPACING - \
            (FOOTER_USER_DEVICE_SPACING // 2)
        recent_timestamp = utils.ellipsize_text(
            options.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            font,
            recent_timestamp_max_width)
        timestamp_width, timestamp_height = draw.textsize(recent_timestamp, font)

        timestamp_x = image.width - PADDING - timestamp_width - \
            FOOTER_ICON_NAME_SPACING - recent_icon_width
        timestamp_y = avatar_image_y + ((avatar_image_height - recent_icon_height) // 2)

        # Now that we've done all of our management, it's time to draw it.
        image.paste(recent_icon, (timestamp_x, timestamp_y))

        # Draw the text
        draw.text(
            (timestamp_x + recent_icon_width + FOOTER_ICON_NAME_SPACING,
             timestamp_y + ((recent_icon_height - timestamp_height) // 2) - 2),
            recent_timestamp, font=font, fill=InkyWHAT.BLACK)
