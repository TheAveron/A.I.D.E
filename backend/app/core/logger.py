import logging
import re
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

_CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")


def log_safe(value: str) -> str:
    """`value` with control characters made visible instead of interpreted.

    A URL path is client input. The URL parser already drops line breaks, but
    other control characters (an ESC that starts a terminal escape sequence,
    NUL, ...) would be written to the log file and to the console as they are.
    """
    return _CONTROL_CHARACTERS.sub(lambda m: f"\\x{ord(m.group()):02x}", value)


def setup_logger(
    name: str, log_file: Optional[Path] = None, level: int = logging.DEBUG
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
