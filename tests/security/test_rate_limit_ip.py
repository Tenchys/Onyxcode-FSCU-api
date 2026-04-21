"""Tests for IP-based rate limiting."""
import asyncio
from unittest.mock import patch

import pytest

from app.security.rate_limit import check_ip_rate_limit, _IP_COUNTER, _LOCK


@pytest.fixture(autouse=True)
def clear_counters():
    """Clear rate limit counters before each test."""
    _IP_COUNTER.clear()
    yield
    _IP_COUNTER.clear()


@pytest.mark.asyncio
async def test_ip_allowed_within_limit():
    """IP should be allowed when under the limit."""
    client_ip = "192.168.1.1"
    allowed, reason = await check_ip_rate_limit(client_ip, window=60, limit=10)
    assert allowed is True
    assert reason is None


@pytest.mark.asyncio
async def test_ip_blocked_when_limit_exceeded():
    """IP should be blocked with 429 when over the limit."""
    client_ip = "192.168.1.2"
    window, limit = 60, 3

    # Exhaust the quota
    for _ in range(limit):
        await check_ip_rate_limit(client_ip, window, limit)

    allowed, reason = await check_ip_rate_limit(client_ip, window, limit)
    assert allowed is False
    assert reason == "429"


@pytest.mark.asyncio
async def test_different_ips_independent():
    """Different IPs should have independent counters."""
    ip_a = "10.0.0.1"
    ip_b = "10.0.0.2"
    window, limit = 60, 2

    for _ in range(limit):
        await check_ip_rate_limit(ip_a, window, limit)

    # ip_b should still be allowed
    allowed, _ = await check_ip_rate_limit(ip_b, window, limit)
    assert allowed is True
