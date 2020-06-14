"""The playwhat module"""

import os
import logging
import logging.config
import sys

import dotenv
import yaml

# Define the root logger for this module
LOGGER = logging.getLogger(__package__)

# Define the Spotify scopes that's needed by PlayingWHAT to work
API_SCOPES = ["user-read-recently-played", "user-read-playback-state"]

# Define the available environment variables keys that should exist in the .env file
ENV_ENV_FILE = "ENV_FILE"
ENV_LOG_CONF = "LOG_CONF_FILE"
ENV_CLIENT_ID = "SPOTIFY_CLIENT_ID"
ENV_CLIENT_SECRET = "SPOTIFY_CLIENT_SECRET"
ENV_REDIRECT_URL = "SPOTIFY_REDIRECT_URL"
ENV_CREDENTIAL_CACHE_PATH = "SPOTIFY_CREDENTIAL_CACHE_PATH"
ENV_USER_TOKEN = "SPOTIFY_USER_TOKEN"
ENV_ROTATE_IMAGE = "ROTATE_IMAGE"

def setup_logging(verbose: bool = False, logger: logging.Logger = LOGGER):
    """
    Initializes a Python module for logging when invoked directly (i.e., typically through
    `__main__`)

    Parameters:
    * `verbose`: Specify if logging should be verbose or not.
    * `logger`: The logger to log messages from this method.
    """
    # Has a logging file been passed through an environment variable?
    logconf_path = os.getenv(ENV_LOG_CONF, None)
    if logconf_path is None:
        # Use the default logging configuration, where we print everything to STDERR
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format="%(asctime)s - [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=sys.stderr
        )

        logger.info("Successfully loaded logging configuration")
    else:
        try:
            # Read the logging configuration from the specified file
            with open(logconf_path, "r") as logconf_file:
                logging.config.dictConfig(yaml.load(logconf_file, yaml.SafeLoader))

            if verbose:
                logger.setLevel(logging.DEBUG)

            logger.info("Successfully loaded logging configuration file \"%s\"", logconf_path)
        except Exception: # pylint: disable=broad-except
            # Something went wrong. Use the default logging configuration, where we print everything
            # to stdout
            logging.basicConfig(
                level=logging.DEBUG if verbose else logging.INFO,
                format="[%(levelname)s] %(asctime)s - %(name)s: %(message)s",
                stream=sys.stdout
            )

            logger.exception("Failed to load logging configuration file \"%s\"", logconf_path)

def setup_environment_vars(logger: logging.Logger = LOGGER) -> str:
    """
    Initializes a Python module with the environment variables from a .ENV file

    Parameters:
    * `logger`: The logger to log messages from this method.

    Returns:
    * The .ENV file that was loaded. If the .ENV was not loaded, then `None` is returned.
    """
    # Has the user specified the .ENV file from the ENV_FILE environment variable?
    dotenv_path = os.getenv("ENV_FILE", None)
    if dotenv_path is None:
        try:
            # Nope. So let's see if we can find it ourselves.
            dotenv_path = dotenv.find_dotenv(raise_error_if_not_found=True)
        except IOError:
            logger.exception("Unable to find .ENV file. Please specify the path to the .ENV file "
                             "by setting an \"ENV_FILE\" environment variable")
            return None

    logger.info("Loading .env file from \"%s\"", dotenv_path)
    dotenv.load_dotenv(dotenv_path)
    return dotenv_path
