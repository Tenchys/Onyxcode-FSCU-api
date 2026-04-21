"""Tests for structured security logging."""
import asyncio
import logging
from unittest.mock import MagicMock, patch

import pytest

from app.core.logging import log_security_event
from app.security.concurrency_guard import _get_semaphore, concurrency_guard, reset_global_semaphore
from app.security.rate_limit import _RUT_COUNTER, check_rut_rate_limit


@pytest.mark.parametrize(
    "event_type,client_ip,normalized_rut,reason,latency_ms",
    [
        (
            "RATE_LIMIT_EXCEEDED",
            "192.168.1.1",
            "12345678-5",
            "IP exceeded limit",
            5.0,
        ),
        (
            "CONCURRENCY_LIMIT",
            None,
            None,
            "Global concurrency limit reached",
            None,
        ),
    ],
)
def test_log_security_event_fields(event_type, client_ip, normalized_rut, reason, latency_ms):
    """Security log should contain all required fields."""
    with patch.object(logging.getLogger("app.core.logging"), "warning") as mock_log:
        log_security_event(event_type, client_ip, normalized_rut, reason, latency_ms)
        mock_log.assert_called_once()
        call_args = mock_log.call_args
        # call_args[0] is the positional args tuple; [0][0] is the format string
        format_str = call_args[0][0]
        assert "security_event" in format_str
        assert "type=" in format_str
        assert "ip=" in format_str
        assert "rut=" in format_str
        assert "reason=" in format_str
        assert "latency_ms=" in format_str


@pytest.mark.asyncio
async def test_rate_limit_block_log_has_minimum_fields_and_latency():
    """Blocked RUT log should include reason and measured latency."""
    _RUT_COUNTER.clear()
    normalized_rut = "12345678-5"

    with patch("app.security.rate_limit.log_security_event") as mock_security_log:
        await check_rut_rate_limit(normalized_rut, window=60, limit=1, burst=0)
        allowed, reason = await check_rut_rate_limit(normalized_rut, window=60, limit=1, burst=0)

    assert allowed is False
    assert reason == "429"
    assert mock_security_log.call_count == 1

    kwargs = mock_security_log.call_args.kwargs
    assert kwargs["event_type"] == "RATE_LIMIT_EXCEEDED"
    assert kwargs["normalized_rut"] == normalized_rut
    assert kwargs["reason"]
    assert kwargs["latency_ms"] is not None


@pytest.mark.asyncio
async def test_concurrency_block_log_has_minimum_fields_and_latency():
    """Blocked concurrency log should include reason and measured latency."""
    reset_global_semaphore()
    cfg = MagicMock()
    cfg.api_max_concurrent_requests = 1
    cfg.api_request_timeout_seconds = 0.01

    with patch("app.security.concurrency_guard.get_settings", return_value=cfg):
        sem = _get_semaphore()
        await sem.acquire()

        with patch("app.security.concurrency_guard.log_security_event") as mock_security_log:
            with pytest.raises(Exception):
                async with concurrency_guard():
                    await asyncio.sleep(0)

        sem.release()

    assert mock_security_log.call_count == 1
    kwargs = mock_security_log.call_args.kwargs
    assert kwargs["event_type"] == "CONCURRENCY_LIMIT"
    assert kwargs["reason"]
    assert kwargs["latency_ms"] is not None
