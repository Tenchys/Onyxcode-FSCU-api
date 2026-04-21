"""Error contract validation tests."""
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.schemas import ErrorResponse
from app.core.errors import register_exception_handlers


@pytest.fixture
def app_with_handlers() -> FastAPI:
    """FastAPI app with error handlers registered."""
    app = FastAPI()
    register_exception_handlers(app)
    return app


def test_error_contract_400(app_with_handlers: FastAPI) -> None:
    """400 Bad Request returns standard error contract."""

    @app_with_handlers.get("/bad-request")
    def raise_bad_request():
        raise HTTPException(status_code=400, detail="Invalid input provided")

    client = TestClient(app_with_handlers, raise_server_exceptions=False)
    response = client.get("/bad-request")

    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
    error = data["error"]
    assert error["code"] == "BAD_REQUEST"
    assert error["message"] == "Invalid input provided"


def test_error_contract_404(app_with_handlers: FastAPI) -> None:
    """404 Not Found returns standard error contract."""

    @app_with_handlers.get("/test-404")
    def raise_not_found():
        raise HTTPException(status_code=404, detail="Resource not found")

    client = TestClient(app_with_handlers, raise_server_exceptions=False)
    response = client.get("/test-404")

    assert response.status_code == 404
    data = response.json()
    assert data["status"] == "error"
    error = data["error"]
    assert error["code"] == "NOT_FOUND"
    assert error["message"] == "Resource not found"


def test_error_contract_429(app_with_handlers: FastAPI) -> None:
    """429 Rate limit exceeded returns standard error contract."""

    @app_with_handlers.get("/rate-limited")
    def raise_rate_limit():
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    client = TestClient(app_with_handlers, raise_server_exceptions=False)
    response = client.get("/rate-limited")

    assert response.status_code == 429
    data = response.json()
    assert data["status"] == "error"
    error = data["error"]
    assert error["code"] == "RATE_LIMIT_EXCEEDED"


def test_error_contract_500(app_with_handlers: FastAPI) -> None:
    """500 Internal server error returns standard contract."""

    @app_with_handlers.get("/oops")
    def raise_internal():
        raise HTTPException(status_code=500, detail="Unexpected error")

    client = TestClient(app_with_handlers, raise_server_exceptions=False)
    response = client.get("/oops")

    assert response.status_code == 500
    data = response.json()
    assert data["status"] == "error"
    error = data["error"]
    assert error["code"] == "INTERNAL_ERROR"
    assert "message" in error
