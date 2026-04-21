"""Endpoint behavior for UTM success/fallback/failure scenarios."""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.rut_lookup import LookupResult, UtmUnavailableError


@pytest.fixture
def client() -> TestClient:
    """Create test client with a fresh app instance."""
    return TestClient(create_app())


def test_endpoint_returns_monto_clp_when_remote_utm_available(client: TestClient) -> None:
    """Service success with fresh UTM data returns 200 and UTM fields."""
    mock_result = LookupResult(
        found=True,
        rut=12345678,
        dv="5",
        nombre="JUAN PEREZ",
        universidad="U. DE CHILE",
        monto_utm=150.5,
        cod_universidad=1,
        monto_clp=9030000.0,
        utm_fecha="2025-03",
    )
    with patch("app.api.v1.rut.lookup_rut_service", new=AsyncMock(return_value=mock_result)):
        response = client.get("/v1/rut/12345678-5")

    assert response.status_code == 200
    body = response.json()
    assert body["found"] is True
    assert body["monto_clp"] == 9030000.0
    assert body["utm_fecha"] == "2025-03"


def test_endpoint_returns_200_when_using_last_valid_fallback(client: TestClient) -> None:
    """Service fallback response still returns successful contract."""
    mock_result = LookupResult(
        found=True,
        rut=12345678,
        dv="5",
        nombre="JUAN PEREZ",
        universidad="U. DE CHILE",
        monto_utm=150.5,
        cod_universidad=1,
        monto_clp=8729000.0,
        utm_fecha="2025-02",
    )
    with patch("app.api.v1.rut.lookup_rut_service", new=AsyncMock(return_value=mock_result)):
        response = client.get("/v1/rut/12345678-5")

    assert response.status_code == 200
    body = response.json()
    assert body["monto_clp"] == 8729000.0
    assert body["utm_fecha"] == "2025-02"


def test_endpoint_returns_controlled_500_when_no_utm_value_available(client: TestClient) -> None:
    """When service cannot resolve UTM at all, endpoint returns standard 500 contract."""
    with patch(
        "app.api.v1.rut.lookup_rut_service",
        new=AsyncMock(side_effect=UtmUnavailableError("UTM value unavailable")),
    ):
        response = client.get("/v1/rut/12345678-5")

    assert response.status_code == 500
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "INTERNAL_ERROR"
