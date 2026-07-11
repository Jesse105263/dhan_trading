import logging
import sys

from app.settings import PIPELINE_SETTINGS


LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | "
    "%(name)s | %(message)s"
)


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(
            logging,
            PIPELINE_SETTINGS.log_level,
        ),
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )