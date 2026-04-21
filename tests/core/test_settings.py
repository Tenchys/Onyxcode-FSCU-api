"""Settings validation tests."""
import pytest
from pydantic import ValidationError

from app.core.settings import Settings


@pytest.fixture
def minimal_env() -> dict:
    """Minimal environment variables for Settings."""
    return {
        "DATABASE_URL": "postgresql+psycopg://user:pass@localhost:5432/db",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "db",
        "POSTGRES_USER": "user",
        "POSTGRES_PASSWORD": "pass",
    }


def test_settings_requires_db_url(minimal_env: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """App must not start when DATABASE_URL is missing."""
    for k, v in minimal_env.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("DATABASE_URL", raising=True)
    with pytest.raises(ValidationError) as exc_info:
        Settings()
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("database_url",) for e in errors)


def test_settings_reject_invalid_rate_limits(minimal_env: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """Rate limits above 1000 must be rejected."""
    for k, v in minimal_env.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "9999")
    with pytest.raises(ValidationError) as exc_info:
        Settings()
    errors = exc_info.value.errors()
    assert any("Rate limit too high" in e["msg"] for e in errors)


def test_settings_accepts_valid_config(minimal_env: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings loads successfully with all required fields."""
    for k, v in minimal_env.items():
        monkeypatch.setenv(k, v)
    settings_obj = Settings()
    assert settings_obj.database_url == "postgresql+psycopg://user:pass@localhost:5432/db"
    assert settings_obj.rate_limit_per_minute == 30  # default


def test_settings_reject_invalid_log_level(minimal_env: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid log level must be rejected."""
    for k, v in minimal_env.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("APP_LOG_LEVEL", "invalid_level")
    with pytest.raises(ValidationError) as exc_info:
        Settings()
    errors = exc_info.value.errors()
    assert any("Invalid log level" in e["msg"] for e in errors)


def test_settings_default_values(minimal_env: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify safe defaults for unset values."""
    for k, v in minimal_env.items():
        monkeypatch.setenv(k, v)
    settings_obj = Settings()
    assert settings_obj.app_log_level == "info"
    assert settings_obj.api_request_timeout_seconds == 5
    assert settings_obj.db_statement_timeout_ms == 3000
