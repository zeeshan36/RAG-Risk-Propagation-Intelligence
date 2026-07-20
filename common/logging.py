"""Structured logging helpers."""
import json
import logging
import sys
from typing import Any, Dict

from common.context import get_correlation_id


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key in ("event_id", "scenario", "request_path"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        return json.dumps(payload, default=str)


def setup_logging(level: str | int = "INFO") -> None:
    """Configure root logger with JSON output on stderr."""
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(_JsonFormatter())
        root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a logger instance."""
    return logging.getLogger(name)
