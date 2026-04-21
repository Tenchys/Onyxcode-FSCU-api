"""Pytest configuration and shared fixtures."""
import os

import pytest


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate each test by clearing and resetting environment variables.

    Before each test: save original env, then clear all env vars used by Settings.
    After each test: restore original env.
    """
    # Vars that Settings reads from environment
    settings_vars = [
        "DATABASE_URL",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "RATE_LIMIT_PER_MINUTE",
        "RATE_LIMIT_PER_IP",
        "RATE_LIMIT_PER_RUT",
        "APP_LOG_LEVEL",
        "APP_ENV",
        "APP_NAME",
        "APP_HOST",
        "APP_PORT",
    ]
    original = {v: os.environ.get(v) for v in settings_vars}
    # Clear so tests start fresh
    for v in settings_vars:
        monkeypatch.delenv(v, raising=False)
    yield
    # Restore
    for v, val in original.items():
        if val is None:
            monkeypatch.delenv(v, raising=False)
        else:
            monkeypatch.setenv(v, val)
