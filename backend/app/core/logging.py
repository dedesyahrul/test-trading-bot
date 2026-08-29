import logging
import logging.config
import json
from app.core.config import settings

# Structured logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "json",
            "filename": "logs/app.log",
        },
    },
    "loggers": {
        "": {
            "level": "INFO",
            "handlers": ["console", "file"],
        },
        "sqlalchemy.engine": {
            "level": "WARNING",
        },
    },
}


def setup_logging():
    """Setup logging configuration."""
    logging.config.dictConfig(LOGGING_CONFIG)
    return logging.getLogger(__name__)


logger = setup_logging()
