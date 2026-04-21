"""Tests for pool configuration and defaults."""
from unittest.mock import patch

import pytest

from app.core.settings import Settings
from app.db import postgres


class TestPoolConfig:
    """Verify pool size and timeout settings are respected."""

    def test_pool_size_has_safe_default(self):
        """Pool size must be >= 1 and not excessive."""
        settings = Settings(
            postgres_host="localhost",
            postgres_db="test",
            postgres_user="user",
            postgres_password="pass",
            database_url="postgresql://user:pass@localhost:5432/test",
        )
        assert settings.db_pool_size >= 1
        assert settings.db_pool_size <= 10

    def test_pool_max_overflow_default(self):
        """Overflow should also be bounded."""
        settings = Settings(
            postgres_host="localhost",
            postgres_db="test",
            postgres_user="user",
            postgres_password="pass",
            database_url="postgresql://user:pass@localhost:5432/test",
        )
        assert settings.db_pool_max_overflow >= 0
        assert settings.db_pool_max_overflow <= 10

    def test_statement_timeout_default(self):
        """Statement timeout must be set and bounded."""
        settings = Settings(
            postgres_host="localhost",
            postgres_db="test",
            postgres_user="user",
            postgres_password="pass",
            database_url="postgresql://user:pass@localhost:5432/test",
        )
        assert settings.db_statement_timeout_ms >= 500

    def test_idle_in_transaction_timeout_default(self):
        """Idle-in-transaction timeout must also be set."""
        settings = Settings(
            postgres_host="localhost",
            postgres_db="test",
            postgres_user="user",
            postgres_password="pass",
            database_url="postgresql://user:pass@localhost:5432/test",
        )
        assert settings.db_idle_in_transaction_timeout_ms >= 500

    def test_async_engine_factory_uses_sqlalchemy_create_async_engine(self):
        """Async engine builder must call SQLAlchemy factory (no recursion)."""
        with patch("app.db.postgres.get_settings") as mock_settings:
            mock_settings.return_value.database_url = "postgresql://user:pass@localhost:5432/test"
            mock_settings.return_value.postgres_host = "localhost"
            mock_settings.return_value.postgres_port = 5432
            mock_settings.return_value.postgres_db = "test"
            mock_settings.return_value.postgres_user = "user"
            mock_settings.return_value.postgres_password = "pass"
            mock_settings.return_value.db_pool_size = 3
            mock_settings.return_value.db_pool_max_overflow = 1
            mock_settings.return_value.app_env = "production"

            with patch("app.db.postgres.sa_create_async_engine") as mock_sa_factory:
                postgres.create_async_engine()

            mock_sa_factory.assert_called_once()
