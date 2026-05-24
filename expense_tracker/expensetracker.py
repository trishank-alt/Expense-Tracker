import sqlite3
import bcrypt
from datetime import datetime


class ExpenseTracker:
    def __init__(self, db="expenses.db"):
        self.conn = sqlite3.connect(db, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # easier dict-like access
        self.cursor = self.conn.cursor()
        self.setup()

    # ---------- SETUP ----------
    def setup(self):
        # USERS
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # EXPENSES
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                notes TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)

        # SETTINGS (per user)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER,
                key TEXT,
                value REAL,
                PRIMARY KEY (user_id, key),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)

        # INDEX (performance)
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_id ON expenses(user_id);
        """)

        self.conn.commit()

    # ---------- AUTH ----------
    def create_user(self, email, password):
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        try:
            self.cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # email already exists

    def verify_user(self, email, password):
        self.cursor.execute(
            "SELECT id, password_hash FROM users WHERE email=?",
            (email,)
        )
        row = self.cursor.fetchone()

        if row and bcrypt.checkpw(password.encode(), row["password_hash"]):
            return row["id"]
        return None

    # ---------- INCOME ----------
    def update_income(self, user_id, new_income):
        self.cursor.execute("""
            INSERT INTO settings (user_id, key, value)
            VALUES (?, 'income', ?)
            ON CONFLICT(user_id, key)
            DO UPDATE SET value=excluded.value;
        """, (user_id, new_income))
        self.conn.commit()

    def get_income(self, user_id):
        self.cursor.execute(
            "SELECT value FROM settings WHERE user_id=? AND key='income'",
            (user_id,)
        )
        row = self.cursor.fetchone()
        return row["value"] if row else 0

    # ---------- EXPENSES ----------
    def add_expense(self, user_id, amount, category, notes=""):
        self.cursor.execute("""
            INSERT INTO expenses (user_id, amount, category, notes)
            VALUES (?, ?, ?, ?);
        """, (user_id, amount, category, notes))
        self.conn.commit()

    def delete_expense(self, user_id, exp_id):
        self.cursor.execute(
            "DELETE FROM expenses WHERE id=? AND user_id=?",
            (exp_id, user_id)
        )
        self.conn.commit()
        return self.cursor.rowcount > 0

    def edit_expense(self, user_id, exp_id, new_amount=None, new_category=None, new_notes=None):
        updates, params = [], []

        if new_amount is not None:
            updates.append("amount=?")
            params.append(new_amount)
        if new_category:
            updates.append("category=?")
            params.append(new_category)
        if new_notes is not None:
            updates.append("notes=?")
            params.append(new_notes)

        if not updates:
            return False

        params.extend([exp_id, user_id])

        sql = f"UPDATE expenses SET {', '.join(updates)} WHERE id=? AND user_id=?"
        self.cursor.execute(sql, params)
        self.conn.commit()
        return self.cursor.rowcount > 0

    def get_expenses(self, user_id):
        
        self.cursor.execute("""
            SELECT id, amount, category, notes, date
            FROM expenses
            WHERE user_id=?
        """, (user_id,))

        rows = self.cursor.fetchall()

        return [dict(row) for row in rows]

    def get_expense_by_id(self, user_id, exp_id):
        self.cursor.execute("""
            SELECT * FROM expenses
            WHERE id=? AND user_id=?
        """, (exp_id, user_id))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_expenses_by_category(self, user_id, category):
        self.cursor.execute("""
            SELECT id, amount, category, notes, date
            FROM expenses
            WHERE user_id=? AND category=?
        """, (user_id, category))
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def total_expenses(self, user_id):
        self.cursor.execute(
            "SELECT SUM(amount) as total FROM expenses WHERE user_id=?",
            (user_id,)
        )
        row = self.cursor.fetchone()
        return row["total"] if row["total"] else 0

    def get_savings(self, user_id):
        return self.get_income(user_id) - self.total_expenses(user_id)

    def category_summary(self, user_id):
        self.cursor.execute("""
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE user_id=?
            GROUP BY category
            ORDER BY total DESC;
        """, (user_id,))
        return [dict(row) for row in self.cursor.fetchall()]

    def monthly_summary(self, user_id, year, month):
        self.cursor.execute("""
            SELECT SUM(amount) as total
            FROM expenses
            WHERE user_id=?
            AND strftime('%Y', date)=?
            AND strftime('%m', date)=?;  
        """, (user_id, str(year), f"{month:02d}"))

        row = self.cursor.fetchone()
        return row["total"] if row["total"] else 0

    def clear_expenses(self, user_id):
        self.cursor.execute(
            "DELETE FROM expenses WHERE user_id=?",
            (user_id,)
        )
        self.conn.commit()

    # ---------- CLEANUP ----------
    def __del__(self):
        self.conn.close()
