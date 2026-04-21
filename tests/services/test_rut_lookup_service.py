"""Tests for rut_lookup service."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.repositories.deudores_repo import DeudorRecord
from app.services.rut_lookup import (
    DatabaseError,
    LookupResult,
    lookup_rut,
)


@pytest.fixture
def mock_settings():
    """Minimal settings for service tests."""
    settings = MagicMock()
    settings.utm_cache_ttl_seconds = 86400
    settings.utm_api_url = "https://api.boostr.cl/economy/indicator/utm.json"
    settings.utm_request_timeout_seconds = 5
    return settings


@pytest.mark.asyncio
class TestLookupRut:
    """Test the lookup_rut service function."""

    async def test_returns_found_true_when_record_exists(self, mock_settings):
        """Should return LookupResult with found=True and data."""
        mock_record = DeudorRecord(
            rut=12345678,
            dv="5",
            nombre="JUAN PEREZ",
            universidad="U. DE CHILE",
            monto_utm=150.5,
            cod_universidad=1,
        )

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.execute = AsyncMock()

        with patch("app.services.rut_lookup.get_settings", return_value=mock_settings), \
             patch("app.services.rut_lookup.find_deudor_by_rut", new=AsyncMock(return_value=mock_record)), \
             patch("app.services.rut_lookup._get_utm_cache") as mock_cache_fn, \
             patch("app.services.rut_lookup.fetch_utm_value") as mock_fetch:
            mock_cache = MagicMock()
            mock_cache.get_fresh.return_value = MagicMock(utm=60000.0, fecha="2025-03")
            mock_cache.get_last_valid.return_value = MagicMock(utm=60000.0, fecha="2025-03")
            mock_cache_fn.return_value = mock_cache
            mock_fetch.return_value = MagicMock(success=True, value=MagicMock(utm=60000.0, fecha="2025-03"))

            with patch("app.services.rut_lookup.get_db_session", return_value=mock_session):
                result = await lookup_rut(12345678, "5")

        assert result.found is True
        assert result.rut == 12345678
        assert result.dv == "5"
        assert result.nombre == "JUAN PEREZ"
        assert result.universidad == "U. DE CHILE"
        assert result.monto_utm == 150.5

    async def test_returns_found_false_when_not_exists(self, mock_settings):
        """Should return LookupResult with found=False when no record."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.execute = AsyncMock()

        with patch("app.services.rut_lookup.get_settings", return_value=mock_settings), \
             patch("app.services.rut_lookup.find_deudor_by_rut", new=AsyncMock(return_value=None)), \
             patch("app.services.rut_lookup._get_utm_cache") as mock_cache_fn, \
             patch("app.services.rut_lookup.fetch_utm_value") as mock_fetch:
            mock_cache = MagicMock()
            mock_cache.get_fresh.return_value = None
            mock_cache.get_last_valid.return_value = None
            mock_cache_fn.return_value = mock_cache
            mock_fetch.return_value = MagicMock(success=False, error_message="timeout")

            with patch("app.services.rut_lookup.get_db_session", return_value=mock_session):
                result = await lookup_rut(99999999, "K")

        assert result.found is False
        assert result.rut == 99999999
        assert result.dv == "K"

    async def test_raises_database_error_on_infrastructure_failure(self, mock_settings):
        """Should wrap infrastructure errors in DatabaseError."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.rut_lookup.get_settings", return_value=mock_settings), \
             patch(
                 "app.services.rut_lookup.find_deudor_by_rut",
                 new=AsyncMock(side_effect=ConnectionError("Connection refused")),
             ), \
             patch("app.services.rut_lookup._get_utm_cache") as mock_cache_fn, \
             patch("app.services.rut_lookup.fetch_utm_value") as mock_fetch:
            mock_cache = MagicMock()
            mock_cache.get_fresh.return_value = None
            mock_cache.get_last_valid.return_value = None
            mock_cache_fn.return_value = mock_cache
            mock_fetch.return_value = MagicMock(success=False, error_message="timeout")

            with patch("app.services.rut_lookup.get_db_session", return_value=mock_session):
                with pytest.raises(DatabaseError) as exc_info:
                    await lookup_rut(12345678, "5")
                assert "Database error" in str(exc_info.value)

    async def test_raises_database_error_on_statement_timeout(self, mock_settings):
        """SQL timeout errors must be wrapped as controlled DatabaseError."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.rut_lookup.get_settings", return_value=mock_settings), \
             patch(
                 "app.services.rut_lookup.find_deudor_by_rut",
                 new=AsyncMock(side_effect=TimeoutError("statement timeout")),
             ), \
             patch("app.services.rut_lookup._get_utm_cache") as mock_cache_fn, \
             patch("app.services.rut_lookup.fetch_utm_value") as mock_fetch:
            mock_cache = MagicMock()
            mock_cache.get_fresh.return_value = None
            mock_cache.get_last_valid.return_value = None
            mock_cache_fn.return_value = mock_cache
            mock_fetch.return_value = MagicMock(success=False, error_message="timeout")

            with patch("app.services.rut_lookup.get_db_session", return_value=mock_session):
                with pytest.raises(DatabaseError) as exc_info:
                    await lookup_rut(12345678, "5")

        assert "Database error" in str(exc_info.value)
