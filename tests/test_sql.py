import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from sql import (
    add_expense,
    add_new_subscription,
    add_saving,
    disable_month_subscription,
    enable_month_subscription,
    get_all_categories_and_values,
    get_current_date,
    get_month_subscriptions_expenses,
    get_month_total_expenses,
    get_savings,
    get_subscriptions_breakdown,
    get_year_expenses,
)


@pytest.mark.asyncio
class TestSQLFunctions:
    @patch("sql.aiosqlite.connect")
    async def test_add_expense_calls_db(self, mock_connect):
        mock_db = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_db

        user_id = 123
        category = "🍔 Fast Food"
        amount = 15.50

        await add_expense(user_id, category, amount)

        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()

        call_args = mock_db.execute.call_args[0]
        assert "INSERT INTO expenses" in call_args[0]
        assert call_args[1][0] == user_id
        assert call_args[1][1] == "🍔 Fast Food"
        assert call_args[1][2] == amount

    @patch("sql.aiosqlite.connect")
    async def test_get_month_total_expenses(self, mock_connect):
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=[250.75])

        mock_db = AsyncMock()
        mock_db.cursor.return_value = mock_cursor
        mock_connect.return_value.__aenter__.return_value = mock_db

        result = await get_month_total_expenses(123)

        assert result == 250.75

    @patch("sql.aiosqlite.connect")
    async def test_get_month_total_expenses_no_data(self, mock_connect):
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=[None])

        mock_db = AsyncMock()
        mock_db.cursor.return_value = mock_cursor
        mock_connect.return_value.__aenter__.return_value = mock_db

        result = await get_month_total_expenses(123)

        assert result == 0.0

    @patch("sql.aiosqlite.connect")
    async def test_get_savings_month(self, mock_connect):
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=[250.75])

        mock_db = AsyncMock()
        mock_db.cursor.return_value = mock_cursor
        mock_connect.return_value.__aenter__.return_value = mock_db

        result = await get_savings(123, True)

        assert result == 250.75

    @patch("sql.aiosqlite.connect")
    async def test_get_savings_month_no_data(self, mock_connect):
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=[None])

        mock_db = AsyncMock()
        mock_db.cursor.return_value = mock_cursor
        mock_connect.return_value.__aenter__.return_value = mock_db

        result = await get_savings(123, True)

        assert result == 0.0

    @patch("sql.aiosqlite.connect")
    async def test_get_savings_year(self, mock_connect):
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=[250.75])

        mock_db = AsyncMock()
        mock_db.cursor.return_value = mock_cursor
        mock_connect.return_value.__aenter__.return_value = mock_db

        result = await get_savings(123, False)

        assert result == 250.75

    @patch("sql.aiosqlite.connect")
    async def test_get_savings_year_no_data(self, mock_connect):
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=[None])

        mock_db = AsyncMock()
        mock_db.cursor.return_value = mock_cursor
        mock_connect.return_value.__aenter__.return_value = mock_db

        result = await get_savings(123, False)

        assert result == 0.0

    async def test_get_current_date(self):
        from datetime import datetime

        date = get_current_date()
        datetime.strptime(date, "%Y-%m-%d")
        assert len(date) == 10

    @patch("sql.aiosqlite.connect")
    async def test_add_new_subscription(self, mock_connect):
        mock_db = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_db

        await add_new_subscription(123, "Netflix", 9.99)

        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()
        call_args = mock_db.execute.call_args[0]
        assert "INSERT INTO subscriptions" in call_args[0]

    @patch("sql.aiosqlite.connect")
    async def test_disable_month_subscription(self, mock_connect):
        mock_db = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_db

        await disable_month_subscription(123, "Netflix")

        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()
        call_args = mock_db.execute.call_args[0]
        assert "UPDATE subscriptions" in call_args[0]
        assert call_args[1][0] == 0  # is_active = 0

    @patch("sql.aiosqlite.connect")
    async def test_enable_month_subscription(self, mock_connect):
        mock_db = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_db

        await enable_month_subscription(123, "Netflix")

        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()
        call_args = mock_db.execute.call_args[0]
        assert "UPDATE subscriptions" in call_args[0]

    @patch("sql.aiosqlite.connect")
    async def test_add_saving(self, mock_connect):
        mock_db = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_db

        await add_saving(123, 100.0)

        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()
        call_args = mock_db.execute.call_args[0]
        assert "INSERT INTO savings" in call_args[0]

    @patch("sql.aiosqlite.connect")
    async def test_get_all_categories_and_values(self, mock_connect):
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            return_value=[("🍔 Fast Food", 100.0), ("🚗 Transport", 50.0)]
        )

        mock_db = AsyncMock()
        mock_db.cursor.return_value = mock_cursor
        mock_connect.return_value.__aenter__.return_value = mock_db

        result = await get_all_categories_and_values(123)

        assert len(result) == 2
        assert result[0] == ("🍔 Fast Food", 100.0)

    @patch("sql.aiosqlite.connect")
    async def test_get_year_expenses(self, mock_connect):
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=[500.0])

        mock_db = AsyncMock()
        mock_db.cursor.return_value = mock_cursor
        mock_connect.return_value.__aenter__.return_value = mock_db

        result = await get_year_expenses(123)

        assert result == 500.0

    @patch("sql.aiosqlite.connect")
    async def test_get_year_expenses_no_data(self, mock_connect):
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=[None])

        mock_db = AsyncMock()
        mock_db.cursor.return_value = mock_cursor
        mock_connect.return_value.__aenter__.return_value = mock_db

        result = await get_year_expenses(123)

        assert result == 0.0

    @patch("sql.aiosqlite.connect")
    async def test_get_subscriptions_breakdown(self, mock_connect):
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            return_value=[("Netflix", 9.99), ("Spotify", 4.99)]
        )

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_cursor
        mock_connect.return_value.__aenter__.return_value = mock_db

        result = await get_subscriptions_breakdown(123, True, True)

        assert len(result) == 2
        assert result[0] == ("Netflix", 9.99)

    @patch("sql.aiosqlite.connect")
    async def test_get_subscriptions_breakdown_without_time_filter(self, mock_connect):
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[("Netflix", 9.99)])

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_cursor
        mock_connect.return_value.__aenter__.return_value = mock_db

        result = await get_subscriptions_breakdown(123, True, False)

        assert len(result) == 1

    @patch("sql.aiosqlite.connect")
    async def test_get_month_subscriptions_expenses(self, mock_connect):
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=[19.98])

        mock_db = AsyncMock()
        mock_db.cursor.return_value = mock_cursor
        mock_connect.return_value.__aenter__.return_value = mock_db

        result = await get_month_subscriptions_expenses(123)

        assert result == 19.98

    @patch("sql.aiosqlite.connect")
    async def test_get_month_subscriptions_expenses_no_data(self, mock_connect):
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=[None])

        mock_db = AsyncMock()
        mock_db.cursor.return_value = mock_cursor
        mock_connect.return_value.__aenter__.return_value = mock_db

        result = await get_month_subscriptions_expenses(123)

        assert result == 0.0
