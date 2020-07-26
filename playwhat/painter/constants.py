"""Define constants needed by the `playwhat.painter` module"""

import os

# The padding size between all areas of the painter
PADDING: int = 10

# The path to where all image assets are
PATH_ASSET_IMAGE: str = os.path.join(os.path.dirname(__file__), "assets", "images")

# The path to where all font assets are
PATH_ASSET_FONT: str = os.path.join(os.path.dirname(__file__), "assets", "fonts")

# The directory to cache images
PATH_IMAGE_CACHE = os.path.join(os.sep, "var", "tmp", "playwhat")

# The heading point size
HEADING_POINT_SIZE: int = 26

# The amount of spacing between the Spotify logo and the heading text
HEADING_LOGO_TEXT_SPACING: int = 10

# The amount of spacing between the repeat and shuffle icon.
HEADING_REPEAT_SHUFFLE_SPACING: int = 5

# The album dimension
CONTENT_ALBUM_DIMENSIONS = (150, 150)

# The amount of spacing after the heading to place the content. If set to None, then the content 
# will be aligned to the middle of the InkyWHAT screen automatically.
CONTENT_START_Y = None

# The point size of the track title
CONTENT_TRACK_POINT_SIZE: int = 22

# The point size of the information shown under the track title
CONTENT_INFO_POINT_SIZE: int = 16

# The amount of spacing to put for the text that is shown next to the album art
CONTENT_ALBUM_ART_INFO_SPACING: int = 10

# The amount of spacing that exists between the track's title and the information to show
# underneat the track.
CONTENT_NAME_INFO_SPACING: int = 30

# The amount of spacing between the icon and the text shown next to it
CONTENT_INFO_ICON_SPACING: int = 5

# The amount of spacing between each info line
CONTENT_INFO_LINE_SPACING: int = 3

# The point size of the footer
FOOTER_POINT_SIZE: int = 18

# The amount of spacing between the icon/avatar and the name
FOOTER_ICON_NAME_SPACING: int = 5

# The amount of spacing between the user's name and their device
FOOTER_USER_DEVICE_SPACING: int = 4

# The amount of spacing between the music icon and the "Nothing Playing" heading
NOT_PLAYING_ICON_SPACING: int = 10

# The point size of the "Nothing Playing" heading font
NOT_PLAYING_HEADING_POINT_SIZE: int = 30

# The amount of spacing between the heading and content text
NOT_PLAYING_HEADING_SPACING: int = 20

# The point size of the info text under the "Nothing Playing" heading font
NOT_PLAYING_CONTENT_POINT_SIZE: int = 20
