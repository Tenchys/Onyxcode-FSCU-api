"""Structured JSON logging for security and operational events."""
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Optional


_RESERVED_LOG_RECORD_ATTRS = set(logging.makeLogRecord({}).__dict__.keys()) | {"message", "asctime"}


class JSONFormatter(logging.Formatter):
    """Formatter that emits log records as JSON objects.

    Each emitted record contains:
        - timestamp: ISO 8601 UTC
        - level: log level name
        - logger: name of the logger
        - message: raw message string
        - extra fields when provided via `extra` dict
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Carry through structured fields passed via `extra=` (attached as LogRecord attrs)
        for key, value in record.__dict__.items():
            if key in _RESERVED_LOG_RECORD_ATTRS or key.startswith("_"):
                continue
            payload[key] = value
        # Attach exc_info when present
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def _build_extra(
    *,
    event_type: Optional[str] = None,
    client_ip: Optional[str] = None,
    normalized_rut: Optional[str] = None,
    method: Optional[str] = None,
    path: Optional[str] = None,
    status_code: Optional[int] = None,
    latency_ms: Optional[float] = None,
    reason: Optional[str] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build a dict intended for logging.Formatter.makeRecord `extra` param."""
    fields = {k: v for k, v in locals().items() if v is not None and k != "kwargs"}
    fields.update(kwargs)
    return fields


def configure_json_logging(log_level: str = "info") -> None:
    """Install JSON formatter on the root logger and all descendants.

    Call once at application startup before any handler is used.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.setLevel(log_level.upper())
    # Replace existing handlers to avoid duplicate entries
    for h in root.handlers[:]:
        root.removeHandler(h)
    root.addHandler(handler)
    # Ensure application loggers propagate to root handler only (no duplicate handlers)
    for name in ["app", "uvicorn", "uvicorn.access"]:
        logger = logging.getLogger(name)
        logger.setLevel(log_level.upper())
        for h in logger.handlers[:]:
            logger.removeHandler(h)
        logger.propagate = True


def log_security_event(
    event_type: str,
    client_ip: Optional[str],
    normalized_rut: Optional[str],
    reason: str,
    latency_ms: Optional[float] = None,
) -> None:
    """Emit a structured security log entry.

    Args:
        event_type: Category of event (e.g., "RATE_LIMIT_EXCEEDED", "CONCURRENCY_LIMIT").
        client_ip: IP address of the requesting client.
        normalized_rut: RUT being queried (if available after parsing).
        reason: Human-readable cause for the event.
        latency_ms: Request latency in milliseconds (optional).
    """
    logger = logging.getLogger("app.security")
    extra = _build_extra(
        event_type=event_type,
        client_ip=client_ip or "unknown",
        normalized_rut=normalized_rut or "N/A",
        reason=reason,
        latency_ms=latency_ms,
    )
    logger.warning("security_event", extra=extra)


def log_request(
    method: str,
    path: str,
    client_ip: str,
    status_code: int,
    latency_ms: float,
    normalized_rut: Optional[str] = None,
) -> None:
    """Emit a structured request log entry.

    Args:
        method: HTTP method (GET, POST, etc.).
        path: Request path.
        client_ip: Client IP address.
        status_code: HTTP response status code.
        latency_ms: Request latency in milliseconds.
        normalized_rut: RUT being queried (optional).
    """
    logger = logging.getLogger("app.requests")
    extra = _build_extra(
        method=method,
        path=path,
        client_ip=client_ip,
        status_code=status_code,
        latency_ms=latency_ms,
        normalized_rut=normalized_rut,
    )
    logger.info("request_completed", extra=extra)
