"""FastAPI application factory and entry point."""
import logging

from fastapi import FastAPI

from app.api.v1 import router as v1_router
from app.core.errors import register_exception_handlers
from app.core.middleware import TimeoutMiddleware, lifespan

log = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Onyxcode FSCU API",
        version="1.0.0",
        lifespan=lifespan,
    )
    # Apply request timeout middleware (5 second default)
    app.add_middleware(TimeoutMiddleware, timeout_seconds=5.0)
    # Register error handlers
    register_exception_handlers(app)
    # Mount API routes
    app.include_router(v1_router, prefix="/v1")
    return app


app = create_app()
