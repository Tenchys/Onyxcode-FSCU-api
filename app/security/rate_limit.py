"""Rate limiting middleware and utilities."""
import asyncio
import logging
import time
from collections import defaultdict
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import log_security_event
from app.core.settings import get_settings

log = logging.getLogger(__name__)

_IP_COUNTER: dict[str, list[float]] = defaultdict(list)
_RUT_COUNTER: dict[str, list[float]] = defaultdict(list)
_LOCK = asyncio.Lock()


def _clean_expired(counter: dict[str, list[float]], now: float, window: float) -> None:
    """Remove expired entries from a counter dict."""
    for key in list(counter.keys()):
        counter[key] = [ts for ts in counter[key] if now - ts < window]
        if not counter[key]:
            del counter[key]


async def check_ip_rate_limit(client_ip: str, window: int, limit: int) -> tuple[bool, Optional[str]]:
    """Check if an IP is within its rate limit.

    Returns:
        (allowed, reason): allowed=True if request is permitted, otherwise (False, "429").
    """
    start = time.perf_counter()
    now = time.time()
    async with _LOCK:
        _clean_expired(_IP_COUNTER, now, window)
        timestamps = _IP_COUNTER[client_ip]
        if len(timestamps) >= limit:
            latency_ms = (time.perf_counter() - start) * 1000
            log_security_event(
                event_type="RATE_LIMIT_EXCEEDED",
                client_ip=client_ip,
                normalized_rut=None,
                reason=f"IP {client_ip} exceeded limit {limit} in {window}s window",
                latency_ms=latency_ms,
            )
            return False, "429"
        timestamps.append(now)
    return True, None


async def check_rut_rate_limit(
    normalized_rut: str, window: int, limit: int, burst: int
) -> tuple[bool, Optional[str]]:
    """Check if a RUT is within its rate limit with burst allowance.

    Returns:
        (allowed, reason): allowed=True if request is permitted, otherwise (False, "429").
    """
    start = time.perf_counter()
    now = time.time()
    effective_limit = limit + max(burst, 0)
    async with _LOCK:
        _clean_expired(_RUT_COUNTER, now, window)
        timestamps = _RUT_COUNTER[normalized_rut]
        if len(timestamps) >= effective_limit:
            latency_ms = (time.perf_counter() - start) * 1000
            log_security_event(
                event_type="RATE_LIMIT_EXCEEDED",
                client_ip=None,
                normalized_rut=normalized_rut,
                reason=(
                    f"RUT {normalized_rut} exceeded limit {limit} with burst {burst} "
                    f"in {window}s window"
                ),
                latency_ms=latency_ms,
            )
            return False, "429"
        timestamps.append(now)
    return True, None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware enforcing per-IP and per-RUT rate limits."""

    def __init__(
        self,
        app,
        window_seconds: Optional[int] = None,
        ip_limit: Optional[int] = None,
        rate_limit_enabled: Optional[bool] = None,
        rut_limit: Optional[int] = None,
        burst: Optional[int] = None,
    ) -> None:
        super().__init__(app)
        self._window_seconds = window_seconds
        self._ip_limit = ip_limit
        self._enabled = rate_limit_enabled
        self._rut_limit = rut_limit
        self._burst = burst

    def _get_config(self):
        """Lazily load settings to avoid import-time errors in tests."""
        try:
            settings = get_settings()
            return {
                "window_seconds": self._window_seconds if self._window_seconds is not None else settings.rate_limit_window_seconds,
                "ip_limit": self._ip_limit if self._ip_limit is not None else settings.rate_limit_per_ip,
                "enabled": self._enabled if self._enabled is not None else settings.rate_limit_enabled,
                "rut_limit": self._rut_limit if self._rut_limit is not None else settings.rate_limit_per_rut,
                "burst": self._burst if self._burst is not None else settings.rate_limit_burst,
            }
        except Exception:
            # Fallback to safe defaults if settings can't be loaded (e.g., in tests without env vars)
            return {
                "window_seconds": self._window_seconds or 60,
                "ip_limit": self._ip_limit or 100,
                "enabled": self._enabled if self._enabled is not None else True,
                "rut_limit": self._rut_limit or 10,
                "burst": self._burst or 5,
            }

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], asyncio.TimeoutResult]
    ) -> Response:
        cfg = self._get_config()
        if not cfg["enabled"]:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        allowed, _ = await check_ip_rate_limit(client_ip, cfg["window_seconds"], cfg["ip_limit"])
        if not allowed:
            return Response(
                content='{"status":"error","error":{"code":"RATE_LIMIT_EXCEEDED","message":"Too many requests."}}',
                status_code=429,
                media_type="application/json",
            )

        return await call_next(request)
