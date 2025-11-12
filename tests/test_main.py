from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from main import start_bot


@pytest.mark.asyncio
class TestMain:
    async def test_start_bot_initializes(self):
        with (
            patch("main.connect_database") as mock_connect,
            patch("main.Bot") as mock_bot_class,
            patch("main.Dispatcher") as mock_dp_class,
            patch("main.MemoryStorage"),
            patch("main.logger"),
            patch("main.main_menu"),
            patch("main.logic_router"),
        ):
            mock_bot = MagicMock()
            mock_bot_class.return_value = mock_bot

            mock_dp = MagicMock()
            mock_dp.message = MagicMock(return_value=lambda func: func)
            mock_dp.include_router = MagicMock()
            mock_dp.start_polling = AsyncMock(
                side_effect=KeyboardInterrupt("Test stop")
            )
            mock_dp_class.return_value = mock_dp

            try:
                await start_bot()
            except KeyboardInterrupt:
                pass

            mock_connect.assert_called_once()
            mock_dp.include_router.assert_called_once()
            mock_dp.start_polling.assert_called_once_with(mock_bot)

    async def test_start_bot_creates_bot_with_token(self):
        with (
            patch("main.connect_database"),
            patch("main.os.getenv", return_value="test_token"),
            patch("main.Bot") as mock_bot_class,
            patch("main.Dispatcher") as mock_dp_class,
            patch("main.MemoryStorage"),
            patch("main.logger"),
            patch("main.main_menu"),
            patch("main.logic_router"),
        ):
            mock_bot = MagicMock()
            mock_bot_class.return_value = mock_bot

            mock_dp = MagicMock()
            mock_dp.message = MagicMock(return_value=lambda func: func)
            mock_dp.start_polling = AsyncMock(
                side_effect=KeyboardInterrupt("Test stop")
            )
            mock_dp_class.return_value = mock_dp

            try:
                await start_bot()
            except KeyboardInterrupt:
                pass

            mock_bot_class.assert_called_once()

    async def test_start_bot_creates_dispatcher(self):
        with (
            patch("main.connect_database"),
            patch("main.Bot") as mock_bot_class,
            patch("main.Dispatcher") as mock_dp_class,
            patch("main.MemoryStorage") as mock_storage_class,
            patch("main.logger"),
            patch("main.main_menu"),
            patch("main.logic_router"),
        ):
            mock_bot = MagicMock()
            mock_bot_class.return_value = mock_bot

            mock_storage = MagicMock()
            mock_storage_class.return_value = mock_storage

            mock_dp = MagicMock()
            mock_dp.message = MagicMock(return_value=lambda func: func)
            mock_dp.start_polling = AsyncMock(
                side_effect=KeyboardInterrupt("Test stop")
            )
            mock_dp_class.return_value = mock_dp

            try:
                await start_bot()
            except KeyboardInterrupt:
                pass

            mock_dp_class.assert_called_once()
            mock_storage_class.assert_called_once()
