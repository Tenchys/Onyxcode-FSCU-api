"""Tests for deudores repository — exact query only."""
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.repositories.deudores_repo import (
    DeudorRecord,
    _EXACT_LOOKUP_SQL,
    find_deudor_by_rut,
)


class TestDeudorRecordFromRow:
    """Test DeudorRecord assembly from DB row."""

    def test_from_row_assembles_full_name(self):
        """Nombre completo is built from nombres + apellido_paterno + apellido_materno."""
        mock_row = MagicMock()
        mock_row.nombres = "JUAN  "
        mock_row.apellido_paterno = "PEREZ"
        mock_row.apellido_materno = "GOMEZ"
        mock_row.rut = "12345678"
        mock_row.dv = "5"
        mock_row.universidad = "U. DE CHILE"
        mock_row.monto_utm = Decimal("150.5")
        mock_row.cod_universidad = 1

        record = DeudorRecord.from_row(mock_row)
        assert record.nombre == "JUAN PEREZ GOMEZ"

    def test_from_row_handles_null_nombres(self):
        """Null nombres should not break name assembly."""
        mock_row = MagicMock()
        mock_row.nombres = None
        mock_row.apellido_paterno = "PEREZ"
        mock_row.apellido_materno = "GOMEZ"
        mock_row.rut = "12345678"
        mock_row.dv = "5"
        mock_row.universidad = "U. DE CHILE"
        mock_row.monto_utm = Decimal("150.5")
        mock_row.cod_universidad = 1

        record = DeudorRecord.from_row(mock_row)
        assert record.nombre == "PEREZ GOMEZ"

    def test_from_row_converts_decimal_to_float(self):
        """monto_utm must be float, not Decimal, for JSON serialization."""
        mock_row = MagicMock()
        mock_row.nombres = "JUAN"
        mock_row.apellido_paterno = "PEREZ"
        mock_row.apellido_materno = "GOMEZ"
        mock_row.rut = "12345678"
        mock_row.dv = "5"
        mock_row.universidad = "U. DE CHILE"
        mock_row.monto_utm = Decimal("150.5000")
        mock_row.cod_universidad = 1

        record = DeudorRecord.from_row(mock_row)
        assert isinstance(record.monto_utm, float)
        assert record.monto_utm == 150.5


class TestExactLookupQuery:
    """Test that the SQL query is fixed and parameterized."""

    def test_query_is_not_dynamic(self):
        """SQL must not contain f-string interpolation or .format()."""
        sql_text = _EXACT_LOOKUP_SQL.text
        assert ":rut" in sql_text
        assert ":dv" in sql_text
        assert "WHERE rut = :rut AND dv = :dv" in sql_text

    def test_query_limits_to_one(self):
        """Query must have LIMIT 1 to avoid unnecessary rows."""
        assert "LIMIT 1" in _EXACT_LOOKUP_SQL.text

    def test_query_selects_only_needed_columns(self):
        """Only domain-relevant columns are selected."""
        sql_text = _EXACT_LOOKUP_SQL.text
        assert "rut" in sql_text
        assert "dv" in sql_text
        assert "nombres" in sql_text
        assert "apellido_paterno" in sql_text
        assert "apellido_materno" in sql_text
        assert "monto_utm" in sql_text
        assert "universidad" in sql_text


@pytest.mark.asyncio
class TestFindDeudorByRut:
    """Test find_deudor_by_rut with a mock session."""

    async def test_returns_record_when_found(self):
        """Should return DeudorRecord when query matches."""
        mock_row = MagicMock()
        mock_row.nombres = "JUAN"
        mock_row.apellido_paterno = "PEREZ"
        mock_row.apellido_materno = "GOMEZ"
        mock_row.rut = "12345678"
        mock_row.dv = "5"
        mock_row.universidad = "U. DE CHILE"
        mock_row.monto_utm = Decimal("150.5")
        mock_row.cod_universidad = 1

        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = mock_row

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        record = await find_deudor_by_rut(mock_session, 12345678, "5")
        assert record is not None
        assert record.rut == 12345678
        assert record.dv == "5"
        assert record.nombre == "JUAN PEREZ GOMEZ"

    async def test_returns_none_when_not_found(self):
        """Should return None when no row matches rut+dv."""
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        record = await find_deudor_by_rut(mock_session, 99999999, "K")
        assert record is None

    async def test_passes_parameters_correctly(self):
        """Query must receive rut and dv as separate parameters."""
        captured_params = None

        async def capture_execute(sql, params=None):
            nonlocal captured_params
            captured_params = params
            mock_result = MagicMock()
            mock_result.mappings.return_value.first.return_value = None
            return mock_result

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=capture_execute)

        await find_deudor_by_rut(mock_session, 12345678, "9")
        assert captured_params == {"rut": "12345678", "dv": "9"}
