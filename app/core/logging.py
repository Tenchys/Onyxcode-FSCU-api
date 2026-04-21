"""Structured logging utilities for security and operational events."""
import logging
from typing import Optional

log = logging.getLogger(__name__)


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
    log.warning(
        "security_event type=%s ip=%s rut=%s reason=%s latency_ms=%s",
        event_type,
        client_ip or "unknown",
        normalized_rut or "N/A",
        reason,
        latency_ms if latency_ms is not None else "N/A",
    )
