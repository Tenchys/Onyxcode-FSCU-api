"""Minimal metrics collection for operational monitoring."""
import logging
import time
from typing import Optional

from app.core.settings import get_settings

log = logging.getLogger(__name__)

# In-memory counters: keyed by status code family or metric name
_API_STATUS_COUNTS: dict[int, int] = {}
_API_LATENCIES: list[float] = []
_UTM_LATENCIES: list[float] = []
_LOCK = __import__("threading").Lock()


def _record_latency(bucket: list[float], latency_ms: float, max_size: int = 1000) -> None:
    """Append a latency sample, keeping list bounded."""
    with _LOCK:
        bucket.append(latency_ms)
        if len(bucket) > max_size:
            del bucket[: max_size // 2]


def record_api_status(status_code: int) -> None:
    """Increment counter for the given HTTP status code."""
    with _LOCK:
        _API_STATUS_COUNTS[status_code] = _API_STATUS_COUNTS.get(status_code, 0) + 1


def record_api_latency(latency_ms: float) -> None:
    """Record an API request latency sample."""
    _record_latency(_API_LATENCIES, latency_ms)


def record_utm_latency(latency_ms: float) -> None:
    """Record a UTM API latency sample."""
    _record_latency(_UTM_LATENCIES, latency_ms)


def _compute_percentile(sorted_samples: list[float], p: float) -> Optional[float]:
    if not sorted_samples:
        return None
    idx = int(len(sorted_samples) * p / 100.0)
    return sorted_samples[min(idx, len(sorted_samples) - 1)]


class Metrics:
    """Snapshot of current metric values."""

    def __init__(
        self,
        status_counts: dict[int, int],
        api_latency_p50: Optional[float],
        api_latency_p95: Optional[float],
        utm_latency_p50: Optional[float],
        utm_latency_p95: Optional[float],
    ) -> None:
        self.status_counts = status_counts
        self.api_latency_p50 = api_latency_p50
        self.api_latency_p95 = api_latency_p95
        self.utm_latency_p50 = utm_latency_p50
        self.utm_latency_p95 = utm_latency_p95

    def to_dict(self) -> dict:
        return {
            "status_counts": self.status_counts,
            "api_latency_p50_ms": self.api_latency_p50,
            "api_latency_p95_ms": self.api_latency_p95,
            "utm_latency_p50_ms": self.utm_latency_p50,
            "utm_latency_p95_ms": self.utm_latency_p95,
        }


def get_metrics() -> Metrics:
    """Return a snapshot of current in-memory metrics."""
    with _LOCK:
        status_counts = dict(_API_STATUS_COUNTS)
        api_sorted = sorted(_API_LATENCIES)
        utm_sorted = sorted(_UTM_LATENCIES)

    return Metrics(
        status_counts=status_counts,
        api_latency_p50=_compute_percentile(api_sorted, 50),
        api_latency_p95=_compute_percentile(api_sorted, 95),
        utm_latency_p50=_compute_percentile(utm_sorted, 50),
        utm_latency_p95=_compute_percentile(utm_sorted, 95),
    )


def reset_metrics() -> None:
    """Clear all in-memory counters. Useful for testing."""
    global _API_STATUS_COUNTS, _API_LATENCIES, _UTM_LATENCIES
    with _LOCK:
        _API_STATUS_COUNTS.clear()
        _API_LATENCIES.clear()
        _UTM_LATENCIES.clear()
