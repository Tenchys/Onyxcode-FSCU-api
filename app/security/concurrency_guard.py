"""Concurrency guard with async semaphore."""
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Callable, Optional

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import log_security_event
from app.core.settings import get_settings

log = logging.getLogger(__name__)

_global_semaphore: Optional[asyncio.Semaphore] = None


def _get_semaphore() -> asyncio.Semaphore:
    """Get or create the global concurrency semaphore."""
    global _global_semaphore
    if _global_semaphore is None:
        try:
            settings = get_settings()
            _global_semaphore = asyncio.Semaphore(settings.api_max_concurrent_requests)
        except Exception:
            # Fallback to a reasonable default for testing
            _global_semaphore = asyncio.Semaphore(20)
    return _global_semaphore


@asynccontextmanager
async def concurrency_guard():
    """Async context manager that enforces a global concurrency limit.

    If the limit is reached, requests wait up to a configured timeout and
    raise a 503 Service Unavailable response.
    """
    semaphore = _get_semaphore()
    try:
        settings = get_settings()
        timeout_seconds = settings.api_request_timeout_seconds
    except Exception:
        timeout_seconds = 5.0
    start = time.perf_counter()
    acquired = False
    try:
        acquired = await asyncio.wait_for(
            semaphore.acquire(),
            timeout=timeout_seconds,
        )
        yield
    except asyncio.TimeoutError:
        latency_ms = (time.perf_counter() - start) * 1000
        log_security_event(
            event_type="CONCURRENCY_LIMIT",
            client_ip=None,
            normalized_rut=None,
            reason="Global concurrency limit reached",
            latency_ms=latency_ms,
        )
        log.warning("Concurrency limit reached: global semaphore blocked")
        raise HTTPException(
            status_code=503,
            detail="Service temporarily overloaded. Please retry.",
        )
    finally:
        if acquired:
            semaphore.release()


class ConcurrencyLimitMiddleware(BaseHTTPMiddleware):
    """Global concurrency limiter middleware for all endpoints."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], asyncio.Future],
    ) -> Response:
        try:
            async with concurrency_guard():
                return await call_next(request)
        except HTTPException as exc:
            if exc.status_code == 503:
                return JSONResponse(
                    status_code=503,
                    content={
                        "status": "error",
                        "error": {
                            "code": "CONCURRENCY_LIMIT_EXCEEDED",
                            "message": str(exc.detail),
                        },
                    },
                )
            raise


def reset_global_semaphore() -> None:
    """Reset the global semaphore (for testing purposes only)."""
    global _global_semaphore
    _global_semaphore = None
