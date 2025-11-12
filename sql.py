import logging
import os
import sqlite3
from datetime import datetime

import aiosqlite
import pandas as pd
from dotenv import load_dotenv

from constants import COLUMN_NAMES

logger = logging.getLogger(__name__)

load_dotenv()

DB_PATH = os.getenv("DB_PATH")


def get_current_date():
    return datetime.now().strftime("%Y-%m-%d")


async def connect_database():
    logger.info("Connecting to database.")
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    category TEXT,
                    amount REAL,
                    date TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS savings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL,
                    date TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT,
                    amount REAL,
                    count INTEGER,
                    is_active BOOLEAN,
                    date TEXT
                )
            """)
            await db.commit()
            logger.info("Connecting to database complete.")

    except Exception as e:
        logger.error(f"Error in connect_database: {e}")
        raise


async def add_expense(user_id: int, category: str, amount: float):
    async with aiosqlite.connect(DB_PATH) as db:
        date = get_current_date()
        await db.execute(
            "INSERT INTO expenses (user_id, category, amount,  date) VALUES (?, ?, ?, ?)",
            (user_id, category, amount, date),
        )
        await db.commit()


async def add_new_subscription(user_id: int, name: str, amount: float):
    async with aiosqlite.connect(DB_PATH) as db:
        date = get_current_date()
        await db.execute(
            "INSERT INTO subscriptions (user_id, name, amount, count, is_active, date) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, name, amount, 1, 1, date),
        )
        await db.commit()


async def disable_month_subscription(user_id: int, name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE subscriptions SET is_active = ? WHERE user_id = ? AND name = ?",
            (0, user_id, name),
        )
        await db.commit()


async def enable_month_subscription(user_id: int, name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        current_date = get_current_date()
        await db.execute(
            """
            UPDATE subscriptions
            SET is_active = 1,
                count = CASE
                    WHEN strftime('%Y-%m', date) < strftime('%Y-%m', 'now') THEN count + 1
                    ELSE count
                END,
                date = CASE
                    WHEN strftime('%Y-%m', date) < strftime('%Y-%m', 'now') THEN ?
                    ELSE date
                END
            WHERE user_id = ? AND name = ?
            """,
            (current_date, user_id, name),
        )
        await db.commit()


async def add_saving(user_id: int, amount: float):
    async with aiosqlite.connect(DB_PATH) as db:
        date = get_current_date()
        await db.execute(
            "INSERT INTO savings (user_id, amount, date) VALUES (?, ?, ?)",
            (user_id, amount, date),
        )
        await db.commit()


async def get_all_categories_and_values(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.cursor()
        await cursor.execute(
            """
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE user_id = ? AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
            GROUP BY category
            ORDER BY total DESC
            """,
            (user_id,),
        )
        return await cursor.fetchall()


async def get_year_expenses(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.cursor()
        await cursor.execute(
            """
            SELECT SUM(total_amount) FROM (
                SELECT SUM(amount) AS total_amount
                FROM expenses
                WHERE user_id = ? AND strftime('%Y', date) = strftime('%Y', 'now')
                UNION ALL
                SELECT SUM(amount*count) AS total_amount
                FROM subscriptions
                WHERE user_id = ? AND amount > 0 AND strftime('%Y', date) = strftime('%Y', 'now')
            )
            """,
            (
                user_id,
                user_id,
            ),
        )
        result = await cursor.fetchone()
        return result[0] if result[0] else 0.0


async def get_subscriptions_breakdown(user_id: int, is_active: bool, time_filter: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        base_query = "SELECT name, SUM(amount) AS total FROM subscriptions WHERE user_id = ? AND is_active = ?"
        grouping = "GROUP BY name ORDER BY total DESC"
        month_filter = "AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')"

        query = base_query

        if time_filter:
            query += month_filter
        query += grouping

        cursor = await db.execute(query, (user_id, is_active))
        return await cursor.fetchall()


async def get_month_subscriptions_expenses(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.cursor()
        await cursor.execute(
            """
        SELECT SUM(amount)
        FROM subscriptions
        WHERE user_id = ? AND is_active = 1 AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
        """,
            (user_id,),
        )
        result = await cursor.fetchone()
        return result[0] if result[0] else 0.0


async def get_month_total_expenses(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.cursor()
        await cursor.execute(
            """
        SELECT SUM(total_amount) FROM (
            SELECT SUM(amount) AS total_amount
            FROM expenses
            WHERE user_id = ? AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
            UNION ALL
            SELECT SUM(amount) AS total_amount
            FROM subscriptions
            WHERE user_id = ? AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
        )
        """,
            (user_id, user_id),
        )
        result = await cursor.fetchone()
        return result[0] if result[0] else 0.0


async def get_savings(user_id: int, is_month_saving: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.cursor()
        body = "SELECT SUM(amount) FROM savings WHERE user_id = ? "
        month_savings = "AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')"
        year_savings = "AND strftime('%Y', date) = strftime('%Y', 'now')"

        query = body + month_savings if is_month_saving else body + year_savings
        await cursor.execute(query, (user_id,))

        result = await cursor.fetchone()
        return result[0] if result[0] else 0.0


async def renew_active_subscriptions():
    date = get_current_date()

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE subscriptions
            SET count = count + 1, date = ?
            WHERE is_active = 1
            AND strftime('%Y-%m', date) < strftime('%Y-%m', 'now')
            """,
            (date,),
        )

        await db.commit()


async def get_dataframes(user_id: int, is_all_time_report: bool):
    try:
        with sqlite3.connect(DB_PATH) as connector:
            select_statement = "SELECT * FROM "
            where_user_id = " WHERE user_id = ?"

            filter_current_month = (
                "AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')"
            )

            dataframes = {}

            tables = ["expenses", "savings", "subscriptions"]

            for table in tables:
                query = (
                    select_statement + table + where_user_id
                    if is_all_time_report
                    else select_statement + table + where_user_id + filter_current_month
                )
                dataframes[table] = pd.read_sql(query, connector, params=(user_id,))

            result = await format_dataframes(dataframes)
            return result

    except Exception as e:
        logger.error(f"Error in get_dataframes: {e}")
        raise


async def format_dataframes(dataframes: dict):
    formatted = {}

    for table_name, df in dataframes.items():
        df = df.drop(columns=["id", "user_id"], errors="ignore")
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d %B %Y")

        df = df.rename(columns=COLUMN_NAMES)
        formatted[table_name] = df

    return formatted


async def create_report(user_id: int, is_all_time_report: bool):
    logger.info("Creating report")

    os.makedirs("reports", exist_ok=True)
    report_path = f"reports/user_{user_id}.xlsx"

    try:
        dataframes = await get_dataframes(user_id, is_all_time_report)
        expenses_df = dataframes.get("expenses")
        savings_df = dataframes.get("savings")
        subscriptions_df = dataframes.get("subscriptions")

        with pd.ExcelWriter(report_path, engine="xlsxwriter") as writer:
            expenses_df.to_excel(writer, sheet_name="Expenses", index=False)
            savings_df.to_excel(writer, sheet_name="Savings", index=False)
            subscriptions_df.to_excel(writer, sheet_name="Subscriptions", index=False)

            workbook = writer.book
            header_format = workbook.add_format(
                {"bold": True, "bg_color": "#4CAF50", "font_color": "white"}
            )

            cell_format = workbook.add_format(
                {
                    "align": "center",
                    "valign": "vcenter",
                }
            )

            sheet_names = [
                ("Expenses", expenses_df),
                ("Savings", savings_df),
                ("Subscriptions", subscriptions_df),
            ]

            for sheet_name, df in sheet_names:
                worksheet = writer.sheets[sheet_name]

                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)

                for row_num in range(1, len(df) + 1):
                    for col_num in range(len(df.columns)):
                        worksheet.write(
                            row_num, col_num, df.iloc[row_num - 1, col_num], cell_format
                        )

                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                worksheet.set_column("A:Z", 15)

        logger.info("Report creation complete.")
        return report_path

    except Exception as e:
        logger.error(f"Error in create_report: {e}", exc_info=True)
        raise
