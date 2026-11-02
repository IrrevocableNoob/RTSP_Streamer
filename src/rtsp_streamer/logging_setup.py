"""Application logging: a rotating file handler whose every record has its
RTSP credentials redacted before it is written.
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .urls import redact_url

LOGGER_NAME = "rtsp_streamer"
_MAX_BYTES = 1_000_000
_BACKUPS = 3


class RedactingFilter(logging.Filter):
    """Render each record and strip any RTSP password before formatting."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_url(record.getMessage())
        record.args = None
        return True


def setup_logging(log_path: str) -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    # Idempotent: drop handlers from a previous call so logs are not duplicated.
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    handler = RotatingFileHandler(
        log_path, maxBytes=_MAX_BYTES, backupCount=_BACKUPS, encoding="utf-8"
    )
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    handler.addFilter(RedactingFilter())
    logger.addHandler(handler)
    return logger
