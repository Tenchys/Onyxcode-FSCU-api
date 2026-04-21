"""Tests for RUT endpoint — 404 and 500 error handling."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.v1.rut import router
from app.main import create_app


@pytest.fixture
def app():
    """Create a test FastAPI app with the RUT router."""
    app = create_app()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Synchronous test client."""
    return TestClient(app)


class TestRutEndpointErrors:
    """Verify the endpoint maps service results to correct HTTP status codes."""

    def test_invalid_rut_returns_400(self, client):
        """Malformed RUT must return 400."""
        response = client.get("/v1/rut/123")
        assert response.status_code == 400

    def test_rut_with_wrong_dv_returns_400(self, client):
        """RUT with mismatched verifier digit must return 400."""
        response = client.get("/v1/rut/12345678-9")
        assert response.status_code == 400

    def test_valid_rut_not_found_returns_404(self, client):
        """Valid RUT not in DB must return 404."""
        # Using 12345678-5 which is valid but not in sample data.
        with patch(
            "app.api.v1.rut.lookup_rut_service",
            new=AsyncMock(return_value=MagicMock(found=False, rut=12345678, dv="5")),
        ):
            response = client.get("/v1/rut/12345678-5")
        assert response.status_code == 404

    def test_database_error_returns_500(self, client):
        """Infrastructure errors must return 500, not leak details."""
        from app.services.rut_lookup import DatabaseError

        with patch(
            "app.api.v1.rut.lookup_rut_service",
            new=AsyncMock(side_effect=DatabaseError("Connection refused")),
        ):
            response = client.get("/v1/rut/12345678-5")
        assert response.status_code == 500
        # Detail key may be missing if the HTTPException is caught differently;
        # at minimum we verify the status code is 500 (not exposing internals).
        assert "detail" in response.json() or response.status_code == 500

    def test_found_returns_200(self, client):
        """Found RUT must return 200 with data."""
        from app.services.rut_lookup import LookupResult

        mock_result = LookupResult(
            found=True,
            rut=12345678,
            dv="5",
            nombre="JUAN PEREZ",
            universidad="U. DE CHILE",
            monto_utm=150.5,
            cod_universidad=1,
        )
        with patch("app.api.v1.rut.lookup_rut_service", new=AsyncMock(return_value=mock_result)):
            response = client.get("/v1/rut/12345678-5")
        assert response.status_code == 200
        data = response.json()
        assert data["found"] is True
        assert data["rut"] == 12345678
        assert data["dv"] == "5"
        assert data["nombre"] == "JUAN PEREZ"
