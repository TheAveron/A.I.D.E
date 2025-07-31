import logging
from logging.handlers import RotatingFileHandler
import sys

from pathlib import Path
from typing import Optional


def setup_logger(
    name: str, log_file: Optional[Path] = None, level: int = logging.INFO
) -> logging.Logger:
    """Configure logger with console and file handlers."""

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10485760, backupCount=5  # 10MB
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
