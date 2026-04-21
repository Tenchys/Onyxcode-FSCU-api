"""Tests for global concurrency guard."""
import asyncio
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi import FastAPI

from app.security.concurrency_guard import (
    ConcurrencyLimitMiddleware,
    concurrency_guard,
    _get_semaphore,
    reset_global_semaphore,
)


@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings to avoid requiring env vars."""
    mock_cfg = MagicMock()
    mock_cfg.api_max_concurrent_requests = 20
    mock_cfg.api_request_timeout_seconds = 5.0
    with patch("app.security.concurrency_guard.get_settings", return_value=mock_cfg):
        yield


def test_reset_global_semaphore():
    """Semaphore should be reset for testing."""
    reset_global_semaphore()
    # No error means success


@pytest.mark.asyncio
async def test_concurrency_guard_allows_within_limit():
    """Concurrency guard should allow requests within limit."""
    reset_global_semaphore()
    async with concurrency_guard():
        await asyncio.sleep(0.01)  # Simulate brief work
    # No error means success


@pytest.mark.asyncio
async def test_concurrency_guard_blocks_when_limit_reached():
    """Concurrency guard should raise controlled 503 when saturated."""
    reset_global_semaphore()
    # Directly use the semaphore to avoid __aexit__ complexity
    sem = _get_semaphore()

    # Acquire all slots
    acquired = []
    for _ in range(20):
        acquired.append(await sem.acquire())

    with pytest.raises(Exception) as exc_info:
        async with concurrency_guard():
            await asyncio.sleep(0)

    assert getattr(exc_info.value, "status_code", None) == 503

    # Release for cleanup
    for a in acquired:
        sem.release()


@pytest.mark.asyncio
async def test_global_middleware_rejects_excess_concurrency_with_503():
    """Global middleware must reject overflow with controlled 503."""
    reset_global_semaphore()
    app = FastAPI()
    app.add_middleware(ConcurrencyLimitMiddleware)

    @app.get("/slow")
    async def slow_endpoint() -> dict[str, str]:
        await asyncio.sleep(0.2)
        return {"status": "ok"}

    cfg = MagicMock()
    cfg.api_max_concurrent_requests = 1
    cfg.api_request_timeout_seconds = 0.05

    with patch("app.security.concurrency_guard.get_settings", return_value=cfg):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            responses = await asyncio.gather(
                client.get("/slow"),
                client.get("/slow"),
                client.get("/slow"),
            )

    status_codes = [response.status_code for response in responses]
    assert 503 in status_codes
