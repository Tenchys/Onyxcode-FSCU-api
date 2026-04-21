"""Health check endpoint tests."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok() -> None:
    """GET /v1/health returns 200 with minimal status payload."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}
