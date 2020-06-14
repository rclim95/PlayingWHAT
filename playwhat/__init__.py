"""The playwhat module"""

# Define the Spotify scopes that's needed by PlayingWHAT to work
API_SCOPES = ["user-read-recently-played", "user-read-playback-state"]

# Define the available environment variables keys that should exist in the .env file
ENV_CLIENT_ID = "SPOTIFY_CLIENT_ID"
ENV_CLIENT_SECRET = "SPOTIFY_CLIENT_SECRET"
ENV_REDIRECT_URL = "SPOTIFY_REDIRECT_URL"
ENV_CREDENTIAL_CACHE_PATH = "SPOTIFY_CREDENTIAL_CACHE_PATH"
ENV_USER_TOKEN = "SPOTIFY_USER_TOKEN"
