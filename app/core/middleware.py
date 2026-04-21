"""Request timeout and lifespan middleware."""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.applications import ASGIApp
from starlette.middleware.base import BaseHTTPMiddleware

log = logging.getLogger(__name__)


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    # Startup: verify configuration and initialize resources
    log.info("Starting Onyxcode FSCU API")
    yield
    # Shutdown: release resources
    log.info("Shutting down Onyxcode FSCU API")
