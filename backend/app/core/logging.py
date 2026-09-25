import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Context variables for tracing request execution across async coroutines
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
tenant_id_ctx: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)
user_id_ctx: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


import re

SENSITIVE_PATTERNS = [
    (re.compile(r"(?i)(bearer\s+)[a-zA-Z0-9\-_.]+"), r"\1***REDACTED***"),
    (re.compile(r'(?i)(password["\']?\s*[:=]\s*["\'])([^"\']+)'), r"\1***REDACTED***"),
    (re.compile(r'(?i)(secret["\']?\s*[:=]\s*["\'])([^"\']+)'), r"\1***REDACTED***"),
    (re.compile(r'(?i)(token["\']?\s*[:=]\s*["\'])([^"\']+)'), r"\1***REDACTED***"),
]


def scrub_sensitive_text(text: str) -> str:
    """Scrub sensitive credentials, tokens, and passwords from log strings."""
    if not isinstance(text, str):
        return text
    clean = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        clean = pattern.sub(replacement, clean)
    return clean


class StructuredJsonFormatter(logging.Formatter):
    """
    JSON Formatter for structured production logging.
    Formats logs into JSON with timestamp, level, service, context variables, and message.
    Automatically scrubs sensitive credentials and tokens.
    """
    def __init__(self, service_name: str = "enermax-backend"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        raw_msg = record.getMessage()
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": scrub_sensitive_text(raw_msg),
        }

        # Add tracing context if set
        req_id = getattr(record, "request_id", None) or request_id_ctx.get()
        if req_id:
            log_entry["request_id"] = req_id

        tenant_id = getattr(record, "tenant_id", None) or tenant_id_ctx.get()
        if tenant_id:
            log_entry["tenant_id"] = tenant_id

        user_id = getattr(record, "user_id", None) or user_id_ctx.get()
        if user_id:
            log_entry["user_id"] = user_id

        duration_ms = getattr(record, "duration_ms", None)
        if duration_ms is not None:
            log_entry["duration_ms"] = round(duration_ms, 2)

        # Include extra payload if present
        if hasattr(record, "event"):
            log_entry["event"] = record.event
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            sanitized = {
                k: ("***REDACTED***" if any(s in k.lower() for s in ["password", "secret", "token", "key", "authorization"]) else v)
                for k, v in record.extra_data.items()
            }
            log_entry["data"] = sanitized

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)



def setup_logging(level: str = "INFO", service_name: str = "enermax-backend") -> None:
    """Setup root logger with StructuredJsonFormatter."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredJsonFormatter(service_name=service_name))
    root_logger.addHandler(console_handler)

    # Silence overly verbose external loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


logger = logging.getLogger("enermax")
