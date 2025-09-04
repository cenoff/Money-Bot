import sqlite3
import os
import sys
from datetime import datetime


def get_base_dir():
    # Если запущено через PyInstaller — путь к распакованному архиву
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    # Иначе обычный режим (dev)
    return os.path.dirname(os.path.abspath(__file__))


DB_PATH = os.path.join(get_base_dir(), "money_tracker.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Таблица трат
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    category TEXT,
    amount REAL,
    date TEXT
)
""")

# Таблица сэкономленного
cursor.execute("""
CREATE TABLE IF NOT EXISTS savings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    date TEXT
)
""")

conn.commit()


# --- Функции как были ---
def add_expense(user_id: int, category: str, amount: float):
    date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "INSERT INTO expenses (user_id, category, amount, date) VALUES (?, ?, ?, ?)",
        (user_id, category, amount, date),
    )
    conn.commit()


def add_saving(user_id: int, amount: float):
    date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "INSERT INTO savings (user_id, amount, date) VALUES (?, ?, ?)",
        (user_id, amount, date),
    )
    conn.commit()


def get_month_expenses(user_id: int):
    cursor.execute(
        """
    SELECT category, SUM(amount)
    FROM expenses
    WHERE user_id = ? AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
    GROUP BY category
    """,
        (user_id,),
    )
    return cursor.fetchall()


def get_month_expenses_by_category(user_id: int, category: str):
    cursor.execute(
        """
    SELECT SUM(amount)
    FROM expenses
    WHERE user_id = ? AND category = ? AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
    """,
        (user_id, category),
    )
    return cursor.fetchone()[0] or 0.0


def get_month_total_expenses(user_id: int):
    cursor.execute(
        """
    SELECT SUM(amount)
    FROM expenses
    WHERE user_id = ? AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
    """,
        (user_id,),
    )
    return cursor.fetchone()[0] or 0.0


def get_month_savings(user_id: int):
    cursor.execute(
        """
    SELECT SUM(amount)
    FROM savings
    WHERE user_id = ? AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
    """,
        (user_id,),
    )
    return cursor.fetchone()[0] or 0.0


def get_year_expenses(user_id: int):
    cursor.execute(
        """
    SELECT category, SUM(amount)
    FROM expenses
    WHERE user_id = ? AND strftime('%Y', date) = strftime('%Y', 'now')
    GROUP BY category
    """,
        (user_id,),
    )
    return cursor.fetchall()
