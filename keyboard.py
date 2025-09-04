from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💸 Потратил всего"), KeyboardButton(text="💰 Сэкономил")],
        [
            KeyboardButton(text="🍔 Хрючево"),
            KeyboardButton(text="🎉 Гульки"),
            KeyboardButton(text="🚬 Пошмокать"),
        ],
        [
            KeyboardButton(text="👕 Тряпье"),
            KeyboardButton(text="🖥 Техника"),
            KeyboardButton(text="💅 Бьюти"),
        ],
        [KeyboardButton(text="👱🏿‍♀️ Шалавы")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выбери действие или категорию",
)


def category_stats_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍔 Хрючево", callback_data="stat_food")],
            [InlineKeyboardButton(text="🚬 Пошмокать", callback_data="stat_smoking")],
            [
                InlineKeyboardButton(
                    text="🎉 Гульки", callback_data="stat_entertainment"
                )
            ],
            [InlineKeyboardButton(text="👕 Тряпье", callback_data="stat_cloth")],
            [InlineKeyboardButton(text="🖥 Техника", callback_data="stat_tech")],
            [InlineKeyboardButton(text="💅 Бьюти", callback_data="stat_beauty")],
            [InlineKeyboardButton(text="👱🏿‍♀️ Шалавы", callback_data="stat_sluts")],
            [
                InlineKeyboardButton(
                    text="📆 Потратил за год", callback_data="stat_year"
                )
            ],
        ]
    )


def saving_options():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Добавить сэкономленное", callback_data="add_saving"
                )
            ]
        ]
    )
