"""Tests for statement_timeout enforcement."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db_session


class TestStatementTimeout:
    """Verify statement_timeout is set on sessions."""

    @pytest.mark.asyncio
    async def test_session_sets_statement_timeout(self):
        """The session should execute SET statement_timeout on acquire."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.close = AsyncMock()

        factory = MagicMock()
        factory.return_value.__aenter__.return_value = mock_session
        factory.return_value.__aexit__.return_value = None

        with patch("app.db.postgres.get_async_session_factory", return_value=factory):
            with patch("app.db.postgres.get_settings") as mock_settings:
                mock_settings.return_value.db_statement_timeout_ms = 3000
                mock_settings.return_value.app_env = "production"

                async with get_db_session() as session:
                    assert session is mock_session
                    mock_session.execute.assert_called()
                    call_args = mock_session.execute.call_args
                    assert "statement_timeout" in str(call_args[0][0].text)

        mock_session.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_timeout_value_from_settings(self):
        """Timeout value must come from settings, not hardcoded."""
        with patch("app.db.postgres.get_settings") as mock_settings:
            mock_settings.return_value.db_statement_timeout_ms = 5000
            mock_settings.return_value.app_env = "production"

            captured_timeout = None

            async def capture_execute(query, params=None):
                nonlocal captured_timeout
                if "statement_timeout" in str(query.text):
                    captured_timeout = int(query.text.split("=")[1].strip())
                return MagicMock()

            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.execute = AsyncMock(side_effect=capture_execute)
            mock_session.close = AsyncMock()

            factory = MagicMock()
            factory.return_value.__aenter__.return_value = mock_session
            factory.return_value.__aexit__.return_value = None

            with patch("app.db.postgres.get_async_session_factory", return_value=factory):
                async with get_db_session():
                    pass

            assert captured_timeout == 5000
