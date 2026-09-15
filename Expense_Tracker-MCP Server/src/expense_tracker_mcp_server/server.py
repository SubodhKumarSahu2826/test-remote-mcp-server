from fastmcp import FastMCP
import os
import sqlite3

# 1. DATABASE PATH

DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "expenses.db"
)

CATEGORIES_PATH = os.path.join(
    os.path.dirname(__file__),
    "categories.json"
)

# 2. CREATE MCP SERVER

mcp = FastMCP("ExpenseTracker")

# 3. INITIALIZE DATABASE

def init_db():
    with sqlite3.connect(DB_PATH) as c:

        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                description TEXT DEFAULT '',
                note TEXT DEFAULT '',
                type TEXT DEFAULT 'expense'
            )
        """)


# Create database when server starts
init_db()

# TOOL 1: ADD EXPENSE

@mcp.tool()
def add_expense(
    date: str,
    amount: float,
    category: str,
    subcategory: str = "",
    description: str = "",
    note: str = ""
):
    """Add a new expense entry to the database."""

    with sqlite3.connect(DB_PATH) as c:

        cur = c.execute(
            """
            INSERT INTO expenses(
                date,
                amount,
                category,
                subcategory,
                description,
                note,
                type
            )
            VALUES(?,?,?,?,?,?,?)
            """,
            (
                date,
                amount,
                category,
                subcategory,
                description,
                note,
                "expense"
            )
        )

        return {
            "status": "ok",
            "message": "Expense added successfully",
            "id": cur.lastrowid
        }


# TOOL 2: LIST EXPENSES

@mcp.tool()
def list_expenses(
    start_date: str,
    end_date: str
):
    """List all expense entries within an inclusive date range."""

    with sqlite3.connect(DB_PATH) as c:

        cur = c.execute(
            """
            SELECT
                id,
                date,
                amount,
                category,
                subcategory,
                description,
                note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            AND type = 'expense'
            ORDER BY date DESC
            """,
            (start_date, end_date)
        )

        cols = [d[0] for d in cur.description]

        return [
            dict(zip(cols, row))
            for row in cur.fetchall()
        ]


# TOOL 3: SUMMARIZE

@mcp.tool()
def summarize():
    """Return a summary of total expenses and expenses by category."""

    with sqlite3.connect(DB_PATH) as c:

        # Total expenses
        cur = c.execute(
            """
            SELECT SUM(amount)
            FROM expenses
            WHERE type = 'expense'
            """
        )

        total = cur.fetchone()[0] or 0


        # Expenses grouped by category
        cur = c.execute(
            """
            SELECT
                category,
                SUM(amount)
            FROM expenses
            WHERE type = 'expense'
            GROUP BY category
            ORDER BY SUM(amount) DESC
            """
        )

        category_rows = cur.fetchall()


        by_category = {
            category: amount
            for category, amount in category_rows
        }


        return {
            "total_expenses": total,
            "by_category": by_category
        }


# TOOL 4: EDIT EXPENSE

@mcp.tool()
def edit_expense(
    expense_id: int,
    date: str,
    amount: float,
    category: str,
    subcategory: str = "",
    description: str = "",
    note: str = ""
):
    """Edit an existing expense using its ID."""

    with sqlite3.connect(DB_PATH) as c:

        cur = c.execute(
            """
            UPDATE expenses
            SET
                date = ?,
                amount = ?,
                category = ?,
                subcategory = ?,
                description = ?,
                note = ?
            WHERE
                id = ?
                AND type = 'expense'
            """,
            (
                date,
                amount,
                category,
                subcategory,
                description,
                note,
                expense_id
            )
        )


        if cur.rowcount == 0:

            return {
                "status": "error",
                "message": f"No expense found with ID {expense_id}"
            }


        return {
            "status": "ok",
            "message": "Expense updated successfully",
            "id": expense_id
        }

# TOOL 5: DELETE EXPENSE

@mcp.tool()
def delete_expense(expense_id: int):
    """Delete an expense using its ID."""

    with sqlite3.connect(DB_PATH) as c:

        cur = c.execute(
            """
            DELETE FROM expenses
            WHERE
                id = ?
                AND type = 'expense'
            """,
            (expense_id,)
        )


        if cur.rowcount == 0:

            return {
                "status": "error",
                "message": f"No expense found with ID {expense_id}"
            }


        return {
            "status": "ok",
            "message": "Expense deleted successfully",
            "id": expense_id
        }


# TOOL 6: ADD CREDIT

@mcp.tool()
def add_credit(
    date: str,
    amount: float,
    category: str,
    description: str = "",
    note: str = ""
):
    """Add money received as a credit/income."""

    with sqlite3.connect(DB_PATH) as c:

        cur = c.execute(
            """
            INSERT INTO expenses(
                date,
                amount,
                category,
                description,
                note,
                type
            )
            VALUES(?,?,?,?,?,?)
            """,
            (
                date,
                amount,
                category,
                description,
                note,
                "credit"
            )
        )


        return {
            "status": "ok",
            "message": "Credit added successfully",
            "id": cur.lastrowid
        }



@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    #Read fresh each time so you can edit the file without restarting
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()

# START MCP SERVER

if __name__ == "__main__":
    mcp.run()