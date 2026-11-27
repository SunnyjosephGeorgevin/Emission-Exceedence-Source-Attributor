
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.core.config import LOG_LEVEL


def setup_logging():

    root_logger = logging.getLogger()

    # Prevent duplicate handlers if logging is configured more than once.
    if getattr(root_logger, "_industrial_logging_configured", False):
        return

    log_directory = Path("logs")
    log_directory.mkdir(parents=True, exist_ok=True)

    log_level = getattr(
        logging,
        LOG_LEVEL.upper(),
        logging.INFO,
    )

    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Display logs in the terminal.
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Save logs to a file, rotating when it reaches 2 MB.
    file_handler = RotatingFileHandler(
        log_directory / "application.log",
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    root_logger._industrial_logging_configured = True

    root_logger.info("Application logging initialized.")
