import pytest

from keyboard import subscriptions_keyboard


@pytest.mark.asyncio
class TestKeyboard:
    async def test_subscriptions_keyboard_empty_list(self):
        keyboard = await subscriptions_keyboard([], True)

        assert len(keyboard.inline_keyboard) == 1
        assert keyboard.inline_keyboard[0][0].text == "⬅️ Back"
        assert keyboard.inline_keyboard[0][0].callback_data == "back_to:subscriptions"

    async def test_subscriptions_keyboard_single_subscription(self):
        keyboard = await subscriptions_keyboard(["Netflix"], True)

        assert len(keyboard.inline_keyboard) == 2
        assert keyboard.inline_keyboard[0][0].text == "Netflix"
        assert keyboard.inline_keyboard[0][0].callback_data == "sub_select:Netflix"

    async def test_subscriptions_keyboard_multiple_subscriptions(self):
        names = ["Netflix", "Spotify", "Disney+", "HBO", "Apple Music"]
        keyboard = await subscriptions_keyboard(names, True)

        all_texts = [btn.text for row in keyboard.inline_keyboard[:-1] for btn in row]
        assert "Netflix" in all_texts
        assert "Spotify" in all_texts
        assert "Disney+" in all_texts
        assert "HBO" in all_texts
        assert "Apple Music" in all_texts

    async def test_subscriptions_keyboard_inactive_callback(self):
        keyboard = await subscriptions_keyboard(["Netflix"], False)

        assert keyboard.inline_keyboard[0][0].callback_data == "sub_enable:Netflix"

    async def test_subscriptions_keyboard_groups_by_three(self):
        names = ["Sub1", "Sub2", "Sub3", "Sub4", "Sub5", "Sub6", "Sub7"]
        keyboard = await subscriptions_keyboard(names, True)

        assert len(keyboard.inline_keyboard[0]) == 3
        assert len(keyboard.inline_keyboard[1]) == 3
        assert len(keyboard.inline_keyboard[2]) == 1
        assert keyboard.inline_keyboard[3][0].text == "⬅️ Back"
