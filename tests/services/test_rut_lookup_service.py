"""Tests for rut_lookup service."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.repositories.deudores_repo import DeudorRecord
from app.services.rut_lookup import (
    DatabaseError,
    LookupResult,
    lookup_rut,
)


@pytest.mark.asyncio
class TestLookupRut:
    """Test the lookup_rut service function."""

    async def test_returns_found_true_when_record_exists(self):
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

        with patch("app.services.rut_lookup.find_deudor_by_rut", new=AsyncMock(return_value=mock_record)):
            with patch("app.services.rut_lookup.get_db_session", return_value=mock_session):
                result = await lookup_rut(12345678, "5")

        assert result.found is True
        assert result.rut == 12345678
        assert result.dv == "5"
        assert result.nombre == "JUAN PEREZ"
        assert result.universidad == "U. DE CHILE"
        assert result.monto_utm == 150.5

    async def test_returns_found_false_when_not_exists(self):
        """Should return LookupResult with found=False when no record."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.execute = AsyncMock()

        with patch("app.services.rut_lookup.find_deudor_by_rut", new=AsyncMock(return_value=None)):
            with patch("app.services.rut_lookup.get_db_session", return_value=mock_session):
                result = await lookup_rut(99999999, "K")

        assert result.found is False
        assert result.rut == 99999999
        assert result.dv == "K"

    async def test_raises_database_error_on_infrastructure_failure(self):
        """Should wrap infrastructure errors in DatabaseError."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "app.services.rut_lookup.find_deudor_by_rut",
            new=AsyncMock(side_effect=ConnectionError("Connection refused")),
        ):
            with patch("app.services.rut_lookup.get_db_session", return_value=mock_session):
                with pytest.raises(DatabaseError) as exc_info:
                    await lookup_rut(12345678, "5")
                assert "Database error" in str(exc_info.value)

    async def test_raises_database_error_on_statement_timeout(self):
        """SQL timeout errors must be wrapped as controlled DatabaseError."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "app.services.rut_lookup.find_deudor_by_rut",
            new=AsyncMock(side_effect=TimeoutError("statement timeout")),
        ):
            with patch("app.services.rut_lookup.get_db_session", return_value=mock_session):
                with pytest.raises(DatabaseError) as exc_info:
                    await lookup_rut(12345678, "5")

        assert "Database error" in str(exc_info.value)
