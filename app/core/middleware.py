"""Request timeout, lifespan, and request-logging middleware."""
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
from fastapi.applications import ASGIApp
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import log_request, log_security_event

log = logging.getLogger(__name__)

# Lazy import to avoid circular dependency at module load time
_metrics_module: Optional[object] = None


def _get_metrics():
    global _metrics_module
    if _metrics_module is None:
        try:
            from app.observability import metrics as m

            _metrics_module = m
        except Exception:
            _metrics_module = None
    return _metrics_module


class TimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces a per-request timeout.

    If a request takes longer than `timeout_seconds`, it is cancelled
    and a controlled 504 response is returned.
    """

    def __init__(self, app: ASGIApp, timeout_seconds: float = 5.0) -> None:
        super().__init__(app)
        self.timeout_seconds = timeout_seconds

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], asyncio.Coroutine]
    ) -> Response:
        try:
            return await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError:
            log.warning("Request %s %s timed out after %ss", request.method, request.url.path, self.timeout_seconds)
            return Response(
                content='{"status":"error","error":{"code":"REQUEST_TIMEOUT","message":"Request timed out."}}',
                status_code=504,
                media_type="application/json",
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that emits a structured log for every processed request."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], asyncio.Coroutine]
    ) -> Response:
        start = time.perf_counter()
        client_ip: Optional[str] = None
        normalized_rut: Optional[str] = None

        if request.client:
            client_ip = request.client.host

        # Extract RUT from path if present (e.g., /v1/rut/12.345.678-5)
        path_parts = request.url.path.strip("/").split("/")
        if len(path_parts) >= 3 and path_parts[1] == "rut":
            normalized_rut = path_parts[2]

        try:
            response = await call_next(request)
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            log_request(
                method=request.method,
                path=request.url.path,
                client_ip=client_ip or "unknown",
                status_code=500,
                latency_ms=latency_ms,
                normalized_rut=normalized_rut,
            )
            m = _get_metrics()
            if m is not None:
                m.record_api_status(500)
                m.record_api_latency(latency_ms)
            raise

        latency_ms = (time.perf_counter() - start) * 1000
        log_request(
            method=request.method,
            path=request.url.path,
            client_ip=client_ip or "unknown",
            status_code=response.status_code,
            latency_ms=latency_ms,
            normalized_rut=normalized_rut,
        )
        m = _get_metrics()
        if m is not None:
            m.record_api_status(response.status_code)
            m.record_api_latency(latency_ms)
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    # Startup: verify configuration and initialize resources
    log.info("Starting Onyxcode FSCU API")
    yield
    # Shutdown: release resources
    log.info("Shutting down Onyxcode FSCU API")
