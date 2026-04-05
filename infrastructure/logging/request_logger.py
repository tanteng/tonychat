"""
Request logging infrastructure for TonyChat.

Provides:
- JSONFormatter: JSON-formatted log output
- setup_logger(name): Configure and return a logger with file + console handlers
- get_logger(name): Retrieve an existing logger by name
- generate_request_id(): Generate a UUID request ID
- set_request_id(id) / get_request_id(): Thread-safe request ID storage via contextvars
"""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any

from contextvars import ContextVar

# Thread-safe request ID storage
_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# Store for existing loggers
_loggers: dict[str, logging.Logger] = {}


class JSONFormatter(logging.Formatter):
    """Format log records as single-line JSON."""

    def __init__(self) -> None:
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach request_id if set
        request_id = _request_id_var.get()
        if request_id is not None:
            log_data["request_id"] = request_id

        # Include extra fields from the record
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        # Include any other extra attributes
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "message",
                "request_id",
                "method",
                "path",
                "status_code",
                "duration_ms",
            ):
                if key not in log_data:
                    log_data[key] = value

        return json.dumps(log_data, default=str)


def generate_request_id() -> str:
    """Generate a UUID request ID."""
    return str(uuid.uuid4())


def set_request_id(request_id: str | None) -> None:
    """Set the request ID for the current context (thread-safe)."""
    _request_id_var.set(request_id)


def get_request_id() -> str | None:
    """Get the request ID for the current context (thread-safe)."""
    return _request_id_var.get()


def setup_logger(name: str) -> logging.Logger:
    """
    Configure and return a logger with JSON output.

    Outputs to:
    - logs/tonychat.log (RotatingFileHandler: 10MB, 5 backups)
    - stdout (StreamHandler for development)

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    # Ensure logs directory exists
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "tonychat.log")

    # File handler: 10MB per file, keep 5 backups
    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())

    # Console handler for development
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(JSONFormatter())

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _loggers[name] = logger
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Retrieve an existing logger by name.

    Args:
        name: Logger name

    Returns:
        Logger instance (returns a new logger if none exists for this name)

    Raises:
        ValueError: If no logger with this name was ever set up
    """
    if name not in _loggers:
        return logging.getLogger(name)
    return _loggers[name]
