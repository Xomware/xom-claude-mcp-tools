"""Logging configuration and utilities."""

import os
import sys
from loguru import logger as loguru_logger
from typing import Optional


def setup_logging(
    level: str = "INFO",
    file_path: Optional[str] = None,
    json_format: bool = False,
) -> None:
    """Configure logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        file_path: Optional file path for logging
        json_format: Whether to use JSON format for logs
    """
    # Remove default handler
    loguru_logger.remove()

    # Configure console output
    log_format = (
        "<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    )
    if json_format:
        log_format = (
            "{{"
            '"timestamp": "{time}", '
            '"level": "{level}", '
            '"module": "{name}:{function}", '
            '"message": "{message}"'
            "}}"
        )

    loguru_logger.add(
        sys.stdout,
        format=log_format,
        level=level,
        colorize=not json_format,
    )

    # Configure file output if specified
    if file_path:
        loguru_logger.add(
            file_path,
            format=log_format,
            level=level,
            rotation="500 MB",
            retention="7 days",
        )

    # Set up error file
    error_file = os.getenv("ERROR_LOG_FILE", "logs/error.log")
    os.makedirs(os.path.dirname(error_file), exist_ok=True)
    loguru_logger.add(
        error_file,
        format=log_format,
        level="ERROR",
        rotation="1 GB",
        retention="30 days",
    )


def get_logger(name: str):
    """Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return loguru_logger.bind(name=name)


# Convenience exports
logger = loguru_logger
