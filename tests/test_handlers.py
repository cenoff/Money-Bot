from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.fsm.context import FSMContext

from logic import (
    add_subscription,
    appear_subscriptions_menu,
    ask_saving_input,
    ask_spend_amount,
    choose_category_for_stats,
    disable_subscription,
    disable_subscription_list,
    enable_subscription,
    go_back,
    parse_amount,
    remove_temp_files,
    reports,
    save_saving_input,
    savings,
    spend_input_amount,
    subscription_name,
    subscription_price,
    subscriptions,
)


@pytest.mark.asyncio
class TestHandlers:
    async def test_ask_spend_amount_sets_state(self):
        message_mock = AsyncMock()
        message_mock.text = "🍔 Fast Food"
        state_mock = AsyncMock(spec=FSMContext)

        await ask_spend_amount(message_mock, state_mock)

        state_mock.update_data.assert_called_once_with(category="🍔 Fast Food")
        state_mock.set_state.assert_called_once()

        message_mock.answer.assert_called_once()
        call_text = message_mock.answer.call_args[0][0]
        assert "🍔 Fast Food" in call_text

    async def test_spend_input_amount_valid(self):
        message_mock = AsyncMock()
        message_mock.text = "15.50"
        message_mock.from_user.id = 32432

        state_mock = AsyncMock(spec=FSMContext)
        state_mock.get_data.return_value = {"category": "🍔 Fast Food"}

        with patch("logic.add_expense") as mock_add:
            await spend_input_amount(message_mock, state_mock)

            mock_add.assert_called_once_with(32432, "🍔 Fast Food", 15.50)
            message_mock.answer.assert_called_once()
            state_mock.clear.assert_called_once()

    async def test_spend_input_amount_invalid(self):
        message_mock = AsyncMock()
        message_mock.text = "blabla"

        state_mock = AsyncMock(spec=FSMContext)

        with patch("logic.add_expense") as mock_add:
            await spend_input_amount(message_mock, state_mock)

            mock_add.assert_not_called()

    async def test_remove_temp_files_exists(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        remove_temp_files(str(test_file))

        assert not test_file.exists()

    async def test_remove_temp_files_not_exists(self):
        remove_temp_files("nonexistent_file.txt")

    async def test_parse_amount_valid(self):
        assert parse_amount("10.5") == 10.5
        assert parse_amount("0.99") == 0.99
        assert parse_amount("32") == 32.0

    async def test_parse_amount_comma(self):
        assert parse_amount("10,5") == 10.5
        assert parse_amount("4,56") == 4.56

    async def test_parse_amount_invalid(self):
        assert parse_amount("dsklgnsldkg") is None
        assert parse_amount("12@$") is None
        assert parse_amount("") is None

    async def test_parse_amount_negative(self):
        assert parse_amount("-0.2") is None
        assert parse_amount("-10") is None

    async def test_go_back_subscriptions(self):
        callback_mock = AsyncMock()
        callback_mock.data = "back_to:subscriptions"
        callback_mock.message = AsyncMock()
        callback_mock.from_user.id = 123
        state_mock = AsyncMock(spec=FSMContext)

        with patch("logic.subscriptions") as mock_subs:
            await go_back(callback_mock, state_mock)

            state_mock.clear.assert_called_once()
            callback_mock.message.delete.assert_called_once()
            mock_subs.assert_called_once_with(callback_mock, 123)

    async def test_choose_category_for_stats(self):
        message_mock = AsyncMock()
        message_mock.from_user.id = 123

        with (
            patch("logic.get_month_total_expenses", return_value=100.0),
            patch("logic.get_savings", return_value=50.0),
            patch("logic.get_year_expenses", return_value=500.0),
            patch("logic.get_all_categories_and_values", return_value=[("food", 50.0)]),
            patch("logic.get_month_subscriptions_expenses", return_value=0.0),
            patch("logic.call_graph_creator", return_value="graphs/test.png"),
            patch("logic.remove_temp_files"),
        ):
            await choose_category_for_stats(message_mock)

            message_mock.answer_photo.assert_called_once()
            call_kwargs = message_mock.answer_photo.call_args[1]
            assert "Statistics" in call_kwargs["caption"]

    async def test_choose_category_for_stats_with_subscriptions(self):
        message_mock = AsyncMock()
        message_mock.from_user.id = 123

        with (
            patch("logic.get_month_total_expenses", return_value=100.0),
            patch("logic.get_savings", return_value=50.0),
            patch("logic.get_year_expenses", return_value=500.0),
            patch("logic.get_all_categories_and_values", return_value=[("food", 50.0)]),
            patch("logic.get_month_subscriptions_expenses", return_value=25.0),
            patch("logic.call_graph_creator", return_value="graphs/test.png"),
            patch("logic.remove_temp_files"),
        ):
            await choose_category_for_stats(message_mock)

            message_mock.answer_photo.assert_called_once()

    async def test_enable_subscription(self):
        callback_mock = AsyncMock()
        callback_mock.data = "sub_enable:Netflix"
        callback_mock.from_user.id = 123
        callback_mock.message = AsyncMock()
        state_mock = AsyncMock(spec=FSMContext)

        with patch("logic.enable_month_subscription") as mock_enable:
            await enable_subscription(callback_mock, state_mock)

            mock_enable.assert_called_once_with(123, "Netflix")
            state_mock.clear.assert_called_once()
            callback_mock.answer.assert_called_once()
            callback_mock.message.delete.assert_called_once()

    async def test_add_subscription_with_inactive(self):
        callback_mock = AsyncMock()
        callback_mock.from_user.id = 123
        callback_mock.message = AsyncMock()
        state_mock = AsyncMock(spec=FSMContext)

        with (
            patch(
                "logic.get_subscriptions_breakdown", return_value=[("Netflix", 9.99)]
            ),
            patch("logic.subscriptions_keyboard") as mock_keyboard,
        ):
            mock_keyboard.return_value = MagicMock()

            await add_subscription(callback_mock, state_mock)

            callback_mock.message.edit_text.assert_called_once()
            state_mock.set_state.assert_called_once()

    async def test_add_subscription_no_inactive(self):
        callback_mock = AsyncMock()
        callback_mock.from_user.id = 123
        callback_mock.message = AsyncMock()
        state_mock = AsyncMock(spec=FSMContext)

        with (
            patch("logic.get_subscriptions_breakdown", return_value=[]),
            patch("logic.subscriptions_keyboard") as mock_keyboard,
        ):
            mock_keyboard.return_value = MagicMock()

            await add_subscription(callback_mock, state_mock)

            callback_mock.message.edit_text.assert_called_once()
            assert (
                "Or select an inactive one"
                not in callback_mock.message.edit_text.call_args[0][0]
            )

    async def test_subscription_name(self):
        message_mock = AsyncMock()
        message_mock.text = "Netflix"
        state_mock = AsyncMock(spec=FSMContext)

        await subscription_name(message_mock, state_mock)

        state_mock.update_data.assert_called_once_with(subscription_name="Netflix")
        state_mock.set_state.assert_called_once()
        message_mock.answer.assert_called_once()

    async def test_subscription_name_with_exception(self):
        message_mock = AsyncMock()
        message_mock.text = "Netflix"
        state_mock = AsyncMock(spec=FSMContext)
        state_mock.update_data.side_effect = ValueError("Test error")

        await subscription_name(message_mock, state_mock)

        message_mock.answer.assert_called_once()
        assert "valid subscription name" in message_mock.answer.call_args[0][0]

    async def test_subscription_price_valid(self):
        message_mock = AsyncMock()
        message_mock.text = "9.99"
        message_mock.from_user.id = 123
        state_mock = AsyncMock(spec=FSMContext)
        state_mock.get_data.return_value = {"subscription_name": "Netflix"}

        with patch("logic.add_new_subscription") as mock_add:
            await subscription_price(message_mock, state_mock)

            mock_add.assert_called_once_with(123, "Netflix", 9.99)
            message_mock.answer.assert_called_once()
            state_mock.clear.assert_called_once()

    async def test_subscription_price_invalid(self):
        message_mock = AsyncMock()
        message_mock.text = "invalid"
        state_mock = AsyncMock(spec=FSMContext)

        with patch("logic.add_new_subscription") as mock_add:
            await subscription_price(message_mock, state_mock)

            mock_add.assert_not_called()
            message_mock.answer.assert_called_once()
            assert "number" in message_mock.answer.call_args[0][0].lower()

    async def test_disable_subscription_list(self):
        callback_mock = AsyncMock()
        callback_mock.from_user.id = 123
        callback_mock.message = AsyncMock()
        state_mock = AsyncMock(spec=FSMContext)

        with (
            patch(
                "logic.get_subscriptions_breakdown", return_value=[("Netflix", 9.99)]
            ),
            patch("logic.subscriptions_keyboard") as mock_keyboard,
        ):
            mock_keyboard.return_value = MagicMock()

            await disable_subscription_list(callback_mock, state_mock)

            callback_mock.message.edit_text.assert_called_once()
            state_mock.set_state.assert_called_once()

    async def test_disable_subscription(self):
        callback_mock = AsyncMock()
        callback_mock.data = "sub_select:Netflix"
        callback_mock.from_user.id = 123
        callback_mock.message = AsyncMock()
        state_mock = AsyncMock(spec=FSMContext)

        with patch("logic.disable_month_subscription") as mock_disable:
            await disable_subscription(callback_mock, state_mock)

            mock_disable.assert_called_once_with(123, "Netflix")
            callback_mock.answer.assert_called_once()
            callback_mock.message.delete.assert_called_once()

    async def test_appear_subscriptions_menu(self):
        message_mock = AsyncMock()
        message_mock.from_user.id = 123

        with patch("logic.subscriptions") as mock_subs:
            await appear_subscriptions_menu(message_mock)

            mock_subs.assert_called_once_with(message_mock, 123)

    async def test_subscriptions_empty(self):
        target_mock = AsyncMock()
        target_mock.message = AsyncMock()

        with (
            patch("logic.get_subscriptions_breakdown", return_value=[]),
            patch("logic.get_month_subscriptions_expenses", return_value=0.0),
        ):
            await subscriptions(target_mock, 123)

            target_mock.message.answer.assert_called_once()
            assert (
                "no active subscriptions"
                in target_mock.message.answer.call_args[0][0].lower()
            )

    async def test_subscriptions_with_data(self):
        target_mock = AsyncMock()
        target_mock.message = AsyncMock()

        with (
            patch(
                "logic.get_subscriptions_breakdown",
                return_value=[("Netflix", 9.99), ("Spotify", 4.99)],
            ),
            patch("logic.get_month_subscriptions_expenses", return_value=14.98),
        ):
            await subscriptions(target_mock, 123)

            target_mock.message.answer.assert_called_once()
            assert "Netflix" in target_mock.message.answer.call_args[0][0]

    async def test_subscriptions_with_message_target(self):
        message_mock = MagicMock()
        delattr(message_mock, "message")
        message_mock.answer = AsyncMock()

        with (
            patch("logic.get_subscriptions_breakdown", return_value=[]),
            patch("logic.get_month_subscriptions_expenses", return_value=0.0),
            patch("logic.category_subscriptions_keyboard"),
        ):
            await subscriptions(message_mock, 123)

            message_mock.answer.assert_called_once()

    async def test_savings(self):
        message_mock = AsyncMock()
        message_mock.from_user.id = 123

        with patch("logic.get_savings", return_value=100.0):
            await savings(message_mock)

            message_mock.answer.assert_called_once()
            assert "Savings" in message_mock.answer.call_args[0][0]

    async def test_ask_saving_input(self):
        callback_mock = AsyncMock()
        callback_mock.message = AsyncMock()
        state_mock = AsyncMock(spec=FSMContext)

        await ask_saving_input(callback_mock, state_mock)

        callback_mock.message.answer.assert_called_once()
        state_mock.set_state.assert_called_once()

    async def test_save_saving_input_valid(self):
        message_mock = AsyncMock()
        message_mock.text = "100.50"
        message_mock.from_user.id = 123
        state_mock = AsyncMock(spec=FSMContext)

        with (
            patch("logic.add_saving") as mock_add,
            patch("logic.get_savings", return_value=200.50),
        ):
            await save_saving_input(message_mock, state_mock)

            mock_add.assert_called_once_with(123, 100.50)
            message_mock.answer.assert_called_once()
            state_mock.clear.assert_called_once()

    async def test_save_saving_input_invalid(self):
        message_mock = AsyncMock()
        message_mock.text = "invalid"
        state_mock = AsyncMock(spec=FSMContext)

        with patch("logic.add_saving") as mock_add:
            await save_saving_input(message_mock, state_mock)

            mock_add.assert_not_called()
            message_mock.answer.assert_called_once()
            assert "number" in message_mock.answer.call_args[0][0].lower()

    async def test_reports_month(self):
        callback_mock = AsyncMock()
        callback_mock.data = "report:month"
        callback_mock.from_user.id = 123
        callback_mock.message = AsyncMock()

        with (
            patch("logic.create_report", return_value="reports/test.xlsx"),
            patch("logic.remove_temp_files"),
        ):
            await reports(callback_mock, AsyncMock())

            callback_mock.answer.assert_called_once()
            callback_mock.message.answer_document.assert_called_once()

    async def test_reports_all_time(self):
        callback_mock = AsyncMock()
        callback_mock.data = "report:all_time"
        callback_mock.from_user.id = 123
        callback_mock.message = AsyncMock()

        with (
            patch("logic.create_report", return_value="reports/test.xlsx"),
            patch("logic.remove_temp_files"),
        ):
            await reports(callback_mock, AsyncMock())

            callback_mock.answer.assert_called_once()
            callback_mock.message.answer_document.assert_called_once()

    async def test_reports_with_exception(self):
        callback_mock = AsyncMock()
        callback_mock.data = "report:month"
        callback_mock.from_user.id = 123
        callback_mock.message = AsyncMock()

        with (
            patch("logic.create_report", side_effect=Exception("Test error")),
            patch("logic.logger") as mock_logger,
        ):
            await reports(callback_mock, AsyncMock())

            mock_logger.error.assert_called_once()
