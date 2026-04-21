"""Tests for UTM API client."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.integrations.utm_client import fetch_utm_value, UtmResult, UtmApiError


@pytest.fixture
def mock_settings():
    """Minimal settings needed for UTM client tests."""
    settings = MagicMock()
    settings.utm_api_url = "https://api.boostr.cl/economy/indicator/utm.json"
    settings.utm_request_timeout_seconds = 5
    return settings


@pytest.mark.asyncio
async def test_fetch_utm_success(mock_settings):
    """Valid API response returns UtmResult with value."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value={
        "data": [{"value": 60000.0, "date": "2025-03"}]
    })

    with patch("app.integrations.utm_client.get_settings", return_value=mock_settings), \
         patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        result = await fetch_utm_value()

    assert result.success is True
    assert result.value is not None
    assert result.value.utm == 60000.0
    assert result.value.fecha == "2025-03"


@pytest.mark.asyncio
async def test_fetch_utm_timeout(mock_settings):
    """Timeout returns failure result without raising."""
    with patch("app.integrations.utm_client.get_settings", return_value=mock_settings), \
         patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        result = await fetch_utm_value()

    assert result.success is False
    assert result.value is None
    assert "timeout" in result.error_message.lower()


@pytest.mark.asyncio
async def test_fetch_utm_http_error(mock_settings):
    """HTTP error returns failure result without raising."""
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("app.integrations.utm_client.get_settings", return_value=mock_settings), \
         patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_exc = httpx.HTTPStatusError("500", request=MagicMock(), response=mock_response)
        mock_client.get = AsyncMock(side_effect=mock_exc)
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        result = await fetch_utm_value()

    assert result.success is False
    assert result.value is None


@pytest.mark.asyncio
async def test_fetch_utm_malformed_payload_missing_data(mock_settings):
    """Missing 'data' key returns failure result."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value={"other": "field"})

    with patch("app.integrations.utm_client.get_settings", return_value=mock_settings), \
         patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        result = await fetch_utm_value()

    assert result.success is False
    assert "Missing or empty 'data'" in result.error_message


@pytest.mark.asyncio
async def test_fetch_utm_malformed_payload_missing_fields(mock_settings):
    """Entry without value/date returns failure result."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value={"data": [{"foo": "bar"}]})

    with patch("app.integrations.utm_client.get_settings", return_value=mock_settings), \
         patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        result = await fetch_utm_value()

    assert result.success is False
    assert "Missing 'value' or 'date'" in result.error_message