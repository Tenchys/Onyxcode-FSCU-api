"""Tests for RUT lookup service with UTM integration."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.rut_lookup import UtmUnavailableError, lookup_rut


class FakeRow:
    """Fake row that DeudorRecord.from_row can consume."""
    def __init__(self):
        self.rut = 12345678
        self.dv = "5"
        self.nombres = "Juan"
        self.apellido_paterno = "Pérez"
        self.apellido_materno = ""
        self.monto_utm = 150.5
        self.cod_universidad = 1
        self.universidad = "Universidad de Chile"


class FakeMappingResult:
    """Simulates result.mappings() returned by SQLAlchemy."""
    def __init__(self, row):
        self._row = row

    def first(self):
        return self._row


class FakeResult:
    """Simulates the result of session.execute()."""
    def __init__(self, row):
        self._mapping_result = FakeMappingResult(row)

    def mappings(self):
        return self._mapping_result


@pytest.fixture
def mock_db_session():
    """Mock async DB session returning a fake row."""
    session = AsyncMock()
    session.execute = AsyncMock(return_value=FakeResult(FakeRow()))
    return session


@pytest.fixture
def mock_settings():
    """Minimal settings for service tests."""
    settings = MagicMock()
    settings.utm_cache_ttl_seconds = 86400
    settings.utm_api_url = "https://api.boostr.cl/economy/indicator/utm.json"
    settings.utm_request_timeout_seconds = 5
    return settings


@pytest.mark.asyncio
async def test_lookup_rut_with_utm_success(mock_db_session, mock_settings):
    """Full success: debtor found and UTM conversion available."""
    with patch("app.services.rut_lookup.get_settings", return_value=mock_settings), \
         patch("app.services.rut_lookup.get_db_session") as mock_get_session, \
         patch("app.services.rut_lookup.fetch_utm_value") as mock_fetch, \
         patch("app.services.rut_lookup._get_utm_cache") as mock_cache_fn:
        mock_get_session.return_value.__aenter__.return_value = mock_db_session

        mock_fetch.return_value = MagicMock(
            success=True,
            value=MagicMock(utm=60000.0, fecha="2025-03")
        )

        mock_cache = MagicMock()
        mock_cache.get_fresh.return_value = None
        mock_cache.get_last_valid.return_value = None
        mock_cache_fn.return_value = mock_cache

        result = await lookup_rut(12345678, "5")

    assert result.found is True
    assert result.rut == 12345678
    assert result.monto_utm == 150.5
    assert result.monto_clp == 9030000.0
    assert result.utm_fecha == "2025-03"


@pytest.mark.asyncio
async def test_lookup_rut_fallback_when_utm_unavailable(mock_db_session, mock_settings):
    """UTM API fails but fallback cache is used."""
    with patch("app.services.rut_lookup.get_settings", return_value=mock_settings), \
         patch("app.services.rut_lookup.get_db_session") as mock_get_session, \
         patch("app.services.rut_lookup.fetch_utm_value") as mock_fetch, \
         patch("app.services.rut_lookup._get_utm_cache") as mock_cache_fn:
        mock_get_session.return_value.__aenter__.return_value = mock_db_session

        mock_fetch.return_value = MagicMock(success=False, error_message="API timeout")

        mock_cache = MagicMock()
        mock_cache.get_fresh.return_value = None
        mock_cache.get_last_valid.return_value = MagicMock(utm=58000.0, fecha="2025-02")
        mock_cache_fn.return_value = mock_cache

        result = await lookup_rut(12345678, "5")

    assert result.found is True
    assert result.monto_clp == 8729000.0  # 150.5 * 58000 rounded


@pytest.mark.asyncio
async def test_lookup_rut_no_cache_no_utm_raises_controlled_error(mock_db_session, mock_settings):
    """UTM unavailable and no fallback raises controlled service error."""
    with patch("app.services.rut_lookup.get_settings", return_value=mock_settings), \
         patch("app.services.rut_lookup.get_db_session") as mock_get_session, \
         patch("app.services.rut_lookup.fetch_utm_value") as mock_fetch, \
         patch("app.services.rut_lookup._get_utm_cache") as mock_cache_fn:
        mock_get_session.return_value.__aenter__.return_value = mock_db_session

        mock_fetch.return_value = MagicMock(success=False, error_message="API timeout")

        mock_cache = MagicMock()
        mock_cache.get_fresh.return_value = None
        mock_cache.get_last_valid.return_value = None
        mock_cache_fn.return_value = mock_cache

        with pytest.raises(UtmUnavailableError):
            await lookup_rut(12345678, "5")


@pytest.mark.asyncio
async def test_lookup_rut_expired_cache_forces_remote_revalidation(mock_db_session, mock_settings):
    """Expired cache (no fresh hit) must call remote API and refresh value."""
    with patch("app.services.rut_lookup.get_settings", return_value=mock_settings), \
         patch("app.services.rut_lookup.get_db_session") as mock_get_session, \
         patch("app.services.rut_lookup.fetch_utm_value") as mock_fetch, \
         patch("app.services.rut_lookup._get_utm_cache") as mock_cache_fn:
        mock_get_session.return_value.__aenter__.return_value = mock_db_session

        mock_fetch.return_value = MagicMock(
            success=True,
            value=MagicMock(utm=61000.0, fecha="2025-04"),
        )

        mock_cache = MagicMock()
        mock_cache.get_fresh.return_value = None
        mock_cache.get_last_valid.return_value = MagicMock(utm=58000.0, fecha="2025-02")
        mock_cache_fn.return_value = mock_cache

        result = await lookup_rut(12345678, "5")

    mock_fetch.assert_awaited_once()
    mock_cache.set.assert_called_once()
    assert result.monto_clp == 9180500.0  # 150.5 * 61000 rounded
    assert result.utm_fecha == "2025-04"


@pytest.mark.asyncio
async def test_lookup_rut_not_found():
    """Debtor not found returns found=False without UTM lookup."""
    session = AsyncMock()
    session.execute = AsyncMock(return_value=FakeResult(None))

    with patch("app.services.rut_lookup.get_db_session") as mock_get_session:
        mock_get_session.return_value.__aenter__.return_value = session

        result = await lookup_rut(99999999, "9")

    assert result.found is False
    assert result.monto_clp is None
