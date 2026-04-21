"""Request timeout middleware tests."""
import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.middleware import TimeoutMiddleware


@pytest.fixture
def slow_app() -> FastAPI:
    """FastAPI app with a slow endpoint that exceeds timeout."""
    app = FastAPI()
    app.add_middleware(TimeoutMiddleware, timeout_seconds=0.1)

    @app.get("/slow")
    async def slow_endpoint():
        await asyncio.sleep(10)  # Deliberately slow
        return {"status": "ok"}

    return app


@pytest.fixture
def fast_app() -> FastAPI:
    """FastAPI app with a fast endpoint."""
    app = FastAPI()
    app.add_middleware(TimeoutMiddleware, timeout_seconds=5.0)

    @app.get("/fast")
    async def fast_endpoint():
        return {"status": "ok"}

    return app


def test_request_timeout_returns_controlled_error(slow_app: FastAPI) -> None:
    """Slow request returns 504 with controlled error payload."""
    client = TestClient(slow_app, raise_server_exceptions=False)
    response = client.get("/slow")
    assert response.status_code == 504
    data = response.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "REQUEST_TIMEOUT"


def test_fast_request_succeeds(fast_app: FastAPI) -> None:
    """Fast request completes within timeout."""
    client = TestClient(fast_app, raise_server_exceptions=False)
    response = client.get("/fast")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
