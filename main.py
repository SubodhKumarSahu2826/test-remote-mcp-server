from fastmcp import FastMCP
import os
import json
import sqlite3
import tempfile
import aiosqlite



# Configuration

# Use DB_PATH from environment if provided.
# Otherwise, use the system temporary directory.
TEMP_DIR = tempfile.gettempdir()

DB_PATH = os.getenv(
    "DB_PATH",
    os.path.join(TEMP_DIR, "expenses.db")
)

CATEGORIES_PATH = os.path.join(
    os.path.dirname(__file__),
    "categories.json"
)


print(f"Database path: {DB_PATH}")


# FastMCP Server

mcp = FastMCP("ExpenseTracker")


# Database Initialization

def init_db():
    """Initialize the SQLite database and expenses table."""

    try:
        # Create the directory if DB_PATH points to a custom location.
        db_directory = os.path.dirname(DB_PATH)

        if db_directory:
            os.makedirs(db_directory, exist_ok=True)

        with sqlite3.connect(DB_PATH) as conn:

            conn.execute("PRAGMA journal_mode=WAL")

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT DEFAULT '',
                    note TEXT DEFAULT ''
                )
                """
            )

            conn.commit()

            # Test that the database is writable.
            conn.execute(
                """
                INSERT INTO expenses
                (date, amount, category)
                VALUES (?, ?, ?)
                """,
                ("2000-01-01", 0, "test")
            )

            conn.execute(
                """
                DELETE FROM expenses
                WHERE category = ?
                """,
                ("test",)
            )

            conn.commit()

            print("Database initialized successfully with write access")

    except Exception as e:
        print(f"Database initialization error: {e}")
        raise


# Initialize database when server starts
init_db()


# TOOL 1 — Add Expense

@mcp.tool()
async def add_expense(
    date: str,
    amount: float,
    category: str,
    subcategory: str = "",
    note: str = ""
) -> dict:
    """
    Add a new expense entry to the database.
    """

    try:
        async with aiosqlite.connect(DB_PATH) as conn:

            cursor = await conn.execute(
                """
                INSERT INTO expenses
                (date, amount, category, subcategory, note)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    date,
                    amount,
                    category,
                    subcategory,
                    note
                )
            )

            expense_id = cursor.lastrowid

            await conn.commit()

            return {
                "status": "success",
                "id": expense_id,
                "message": "Expense added successfully"
            }

    except Exception as e:

        if "readonly" in str(e).lower():

            return {
                "status": "error",
                "message": "Database is in read-only mode."
            }

        return {
            "status": "error",
            "message": f"Database error: {str(e)}"
        }


# TOOL 2 — List Expenses

@mcp.tool()
async def list_expenses(
    start_date: str,
    end_date: str
) -> list:
    """
    List all expenses within an inclusive date range.
    """

    try:
        async with aiosqlite.connect(DB_PATH) as conn:

            cursor = await conn.execute(
                """
                SELECT
                    id,
                    date,
                    amount,
                    category,
                    subcategory,
                    note
                FROM expenses
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC, id DESC
                """,
                (
                    start_date,
                    end_date
                )
            )

            rows = await cursor.fetchall()

            columns = [
                column[0]
                for column in cursor.description
            ]

            return [
                dict(zip(columns, row))
                for row in rows
            ]

    except Exception as e:

        return {
            "status": "error",
            "message": f"Error listing expenses: {str(e)}"
        }


# TOOL 3 — Summarize Expenses

@mcp.tool()
async def summarize(
    start_date: str,
    end_date: str,
    category: str | None = None
) -> list:
    """
    Summarize expenses by category within an inclusive date range.
    """

    try:
        async with aiosqlite.connect(DB_PATH) as conn:

            query = """
                SELECT
                    category,
                    SUM(amount) AS total_amount,
                    COUNT(*) AS count
                FROM expenses
                WHERE date BETWEEN ? AND ?
            """

            params = [
                start_date,
                end_date
            ]

            if category:

                query += """
                    AND category = ?
                """

                params.append(category)

            query += """
                GROUP BY category
                ORDER BY total_amount DESC
            """

            cursor = await conn.execute(
                query,
                params
            )

            rows = await cursor.fetchall()

            columns = [
                column[0]
                for column in cursor.description
            ]

            return [
                dict(zip(columns, row))
                for row in rows
            ]

    except Exception as e:

        return {
            "status": "error",
            "message": f"Error summarizing expenses: {str(e)}"
        }


# RESOURCE — Categories

@mcp.resource(
    "expense:///categories",
    mime_type="application/json"
)
def categories() -> str:
    """
    Provide expense categories and subcategories
    from categories.json.
    """

    try:

        with open(
            CATEGORIES_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            return file.read()

    except FileNotFoundError:

        default_categories = {
            "version": "1.0",
            "categories": {
                "Food & Dining": [
                    "Groceries",
                    "Restaurants",
                    "Fast Food",
                    "Cafes & Coffee"
                ],
                "Transportation": [
                    "Fuel",
                    "Public Transport",
                    "Taxi & Cab"
                ],
                "Shopping": [
                    "Clothing",
                    "Electronics",
                    "Online Shopping"
                ],
                "Entertainment": [
                    "Movies",
                    "Games",
                    "Subscriptions"
                ],
                "Bills & Utilities": [
                    "Electricity",
                    "Water",
                    "Internet",
                    "Mobile Phone"
                ],
                "Healthcare": [
                    "Doctor",
                    "Medicines",
                    "Hospital"
                ],
                "Travel": [
                    "Flights",
                    "Hotels",
                    "Local Transport"
                ],
                "Education": [
                    "Courses",
                    "Books",
                    "Training"
                ],
                "Other": [
                    "Miscellaneous"
                ]
            }
        }

        return json.dumps(
            default_categories,
            indent=2
        )

    except Exception as e:

        return json.dumps(
            {
                "status": "error",
                "message": f"Could not load categories: {str(e)}"
            }
        )


# Start Server

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000
    )