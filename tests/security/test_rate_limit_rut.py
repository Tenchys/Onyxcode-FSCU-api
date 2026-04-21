"""Tests for RUT-based rate limiting."""
import pytest

from app.security.rate_limit import check_rut_rate_limit, _RUT_COUNTER


@pytest.fixture(autouse=True)
def clear_counters():
    """Clear rate limit counters before each test."""
    _RUT_COUNTER.clear()
    yield
    _RUT_COUNTER.clear()


@pytest.mark.asyncio
async def test_rut_allowed_within_limit():
    """RUT should be allowed when under the limit."""
    normalized_rut = "12345678-5"
    allowed, reason = await check_rut_rate_limit(normalized_rut, window=60, limit=5, burst=3)
    assert allowed is True
    assert reason is None


@pytest.mark.asyncio
async def test_rut_blocked_when_limit_exceeded():
    """RUT should be blocked with 429 when over the limit."""
    normalized_rut = "12345678-K"
    window, limit = 60, 2

    for _ in range(limit):
        await check_rut_rate_limit(normalized_rut, window, limit, burst=0)

    allowed, reason = await check_rut_rate_limit(normalized_rut, window, limit, burst=0)
    assert allowed is False
    assert reason == "429"


@pytest.mark.asyncio
async def test_different_ruts_independent():
    """Different RUTs should have independent counters."""
    rut_a = "11111111-1"
    rut_b = "22222222-2"
    window, limit = 60, 2

    for _ in range(limit):
        await check_rut_rate_limit(rut_a, window, limit, burst=3)

    # rut_b should still be allowed
    allowed, _ = await check_rut_rate_limit(rut_b, window, limit, burst=3)
    assert allowed is True


@pytest.mark.asyncio
async def test_rut_burst_allows_extra_requests_before_blocking():
    """Burst should increase effective allowance before 429."""
    normalized_rut = "98765432-1"
    window, limit, burst = 60, 2, 1

    for _ in range(limit + burst):
        allowed, _ = await check_rut_rate_limit(normalized_rut, window, limit, burst=burst)
        assert allowed is True

    blocked, reason = await check_rut_rate_limit(normalized_rut, window, limit, burst=burst)
    assert blocked is False
    assert reason == "429"
