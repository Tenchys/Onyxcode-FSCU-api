"""FastAPI application factory and entry point."""
import logging

from fastapi import FastAPI

from app.api.v1 import router as v1_router
from app.core.errors import register_exception_handlers
from app.core.logging import configure_json_logging
from app.core.middleware import RequestLoggingMiddleware, TimeoutMiddleware, lifespan
from app.observability.metrics import get_metrics
from app.security.concurrency_guard import ConcurrencyLimitMiddleware
from app.security.rate_limit import RateLimitMiddleware

log = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Configure structured JSON logging first
    configure_json_logging(log_level="info")

    app = FastAPI(
        title="Onyxcode FSCU API",
        version="1.0.0",
        lifespan=lifespan,
    )
    # Apply request logging middleware (before timeout to capture real latency)
    app.add_middleware(RequestLoggingMiddleware)
    # Apply request timeout middleware (5 second default)
    app.add_middleware(TimeoutMiddleware, timeout_seconds=5.0)
    # Apply rate limit middleware
    app.add_middleware(RateLimitMiddleware)
    # Apply global concurrency limiter
    app.add_middleware(ConcurrencyLimitMiddleware)
    # Register error handlers
    register_exception_handlers(app)
    # Mount API routes
    app.include_router(v1_router, prefix="/v1")

    @app.get("/metrics", tags=["observability"])
    def metrics_endpoint() -> dict:
        """Internal metrics endpoint for operational monitoring."""
        return get_metrics().to_dict()

    return app


app = create_app()
