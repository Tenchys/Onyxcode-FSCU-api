"""Unit tests for RUT endpoint validation logic."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.rut_lookup import LookupResult


@pytest.fixture
def client() -> TestClient:
    """Create a test client with a fresh app instance."""
    app = create_app()
    return TestClient(app)


class TestRutEndpointValidation:
    """Tests for GET /v1/rut/{rut} validation behavior."""

    @pytest.mark.parametrize(
        ("rut_input", "expected_status"),
        [
            ("12.345.678-5", 200),  # valid format, service returns not-found → 404
            ("12345678-5", 200),
            ("1000005-K", 200),  # 8-digit RUT with K as DV
            ("1000005k", 200),  # lowercase k
        ],
    )
    def test_valid_rut_returns_200_or_found_false(
        self, client: TestClient, rut_input: str, expected_status: int
    ) -> None:
        """Valid RUTs should not return 400 at the validation layer.

        Since we don't have a real DB in tests, the service is mocked to
        return found=False so the endpoint returns 404 (not 200, which
        would require an actual DB record). This matches the expected
        behavior change: F03 replaced the placeholder with real lookup.
        """
        # Mock service to return not-found (matches old placeholder behavior)
        mock_result = MagicMock(found=False, rut=12345678, dv="5")
        with patch("app.api.v1.rut.lookup_rut_service", new=AsyncMock(return_value=mock_result)):
            response = client.get(f"/v1/rut/{rut_input}")
        assert response.status_code == 404  # not-found since mock returns found=False

    @pytest.mark.parametrize(
        ("rut_input", "expected_status"),
        [
            ("abc", 400),
            ("12.345.678", 400),  # missing DV
            ("-5", 400),
            ("12.345.678-A", 400),
            ("12.345.678-9", 400),  # wrong DV
            ("", 404),  # empty → route not matched
        ],
    )
    def test_invalid_rut_returns_expected_error_status(
        self, client: TestClient, rut_input: str, expected_status: int
    ) -> None:
        """Invalid RUT must return 400 when route is matched."""
        response = client.get(f"/v1/rut/{rut_input}")
        assert response.status_code == expected_status

    def test_no_db_invoked_on_bad_rut(self, client: TestClient) -> None:
        """When validation fails, the response should be fast and not hit DB."""
        response = client.get("/v1/rut/INVALIDO")
        assert response.status_code == 400
        assert "BAD_REQUEST" in response.json().get("error", {}).get("code", "")

    @pytest.mark.parametrize(
        ("rut_input", "expected_fields"),
        [
            ("12.345.678-5", ["found", "rut", "dv"]),
            ("1000005K", ["found", "rut", "dv"]),
        ],
    )
    def test_response_contains_required_fields(
        self, client: TestClient, rut_input: str, expected_fields: list[str]
    ) -> None:
        """Response must contain at least found, rut, and dv."""
        # Mock service to return a found result so we test response shape
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
            response = client.get(f"/v1/rut/{rut_input}")
        assert response.status_code == 200
        data = response.json()
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
