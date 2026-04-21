"""Centralized settings with strict validation."""
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All critical fields raise at startup if missing or invalid.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_readonly=True,
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = Field(default="onyxcode-fscu-api")
    app_env: str = Field(default="production")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    app_log_level: str = Field(default="info")

    # API controls
    api_prefix: str = Field(default="/v1")
    api_max_concurrent_requests: int = Field(default=20, ge=1)
    api_request_timeout_seconds: int = Field(default=5, ge=1)

    # Rate limit
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_per_minute: int = Field(default=30, ge=1)
    rate_limit_per_ip: int = Field(default=20, ge=1)
    rate_limit_per_rut: int = Field(default=5, ge=1)
    rate_limit_burst: int = Field(default=5, ge=1)
    rate_limit_window_seconds: int = Field(default=60, ge=1)

    # UTM conversion
    utm_api_url: str = Field(default="https://api.boostr.cl/economy/indicator/utm.json")
    utm_cache_ttl_seconds: int = Field(default=86400, ge=1)
    utm_request_timeout_seconds: int = Field(default=5, ge=1)

    # Postgres
    postgres_host: str
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    postgres_db: str
    postgres_user: str
    postgres_password: str
    database_url: str

    # DB timeouts / pool
    db_statement_timeout_ms: int = Field(default=3000, ge=500)
    db_idle_in_transaction_timeout_ms: int = Field(default=5000, ge=500)
    db_pool_size: int = Field(default=5, ge=1)
    db_pool_max_overflow: int = Field(default=5, ge=0)

    @field_validator("app_log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"debug", "info", "warning", "error", "critical"}
        if v.lower() not in allowed:
            raise ValueError(f"Invalid log level: {v}. Must be one of {allowed}.")
        return v.lower()

    @field_validator("rate_limit_per_minute", "rate_limit_per_ip", "rate_limit_per_rut")
    @classmethod
    def validate_rate_limits(cls, v: int) -> int:
        if v > 1000:
            raise ValueError(f"Rate limit too high: {v}. Max allowed is 1000.")
        return v


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
