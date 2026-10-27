from raw.src.config.constants import LOG_BACKUP_COUNT, LOG_FILE, LOG_MAX_BYTES
from logging.handlers import RotatingFileHandler
import logging

LOG_LEVEL: str = "INFO"

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)-8s | %(module)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            LOG_FILE,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        ),
    ],
)


def get_logger(name: str) -> logging.Logger:
    """Returns the logger of a module."""
    return logging.getLogger(name)
