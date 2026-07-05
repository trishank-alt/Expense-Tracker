import sqlite3
import bcrypt
from datetime import datetime


class ExpenseTracker:
    def __init__(self, db="expenses.db"):
        self.conn = sqlite3.connect(db, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # easier dict-like access
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.setup()

    # ---------- SETUP ----------
    def setup(self):
        cur = self.conn.cursor()
        # USERS
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # EXPENSES
        cur.execute("""
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
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER,
                key TEXT,
                value REAL,
                PRIMARY KEY (user_id, key),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)

        # INDEX (performance)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_id ON expenses(user_id);
        """)

        self.conn.commit()

    # ---------- AUTH ----------
    def create_user(self, email, password):
        email = email.lower()
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        try:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # email already exists

    def verify_user(self, email, password):
        email = email.strip().lower()
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, password_hash FROM users WHERE email=?",
            (email,)
        )
        row = cur.fetchone()

        if row and bcrypt.checkpw(password.encode(), row["password_hash"]):
            return row["id"]
        return None

    # ---------- INCOME ----------
    def update_income(self, user_id, new_income):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO settings (user_id, key, value)
            VALUES (?, 'income', ?)
            ON CONFLICT(user_id, key)
            DO UPDATE SET value=excluded.value;
        """, (user_id, new_income))
        self.conn.commit()

    def get_income(self, user_id):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT value FROM settings WHERE user_id=? AND key='income'",
            (user_id,)
        )
        row = cur.fetchone()
        return row["value"] if row else 0

    # ---------- EXPENSES ----------
    def add_expense(self, user_id, amount, category, notes=""):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO expenses (user_id, amount, category, notes)
            VALUES (?, ?, ?, ?);
        """, (user_id, amount, category, notes))
        self.conn.commit()
        cur.execute(
            "SELECT id, amount, category, notes, date FROM expenses WHERE id=?",
            (cur.lastrowid,)
        )
        return dict(cur.fetchone())

    def delete_expense(self, user_id, exp_id):
        cur = self.conn.cursor()
        cur.execute(
            "DELETE FROM expenses WHERE id=? AND user_id=?",
            (exp_id, user_id)
        )
        self.conn.commit()
        return cur.rowcount > 0

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

        cur = self.conn.cursor()
        sql = f"UPDATE expenses SET {', '.join(updates)} WHERE id=? AND user_id=?"
        cur.execute(sql, params)
        self.conn.commit()
        return cur.rowcount > 0

    def get_expenses(self, user_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, amount, category, notes, date
            FROM expenses
            WHERE user_id=?
        """, (user_id,))

        rows = cur.fetchall()

        return [dict(row) for row in rows]

    def get_expense_by_id(self, user_id, exp_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM expenses
            WHERE id=? AND user_id=?
        """, (exp_id, user_id))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_expenses_by_category(self, user_id, category):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, amount, category, notes, date
            FROM expenses
            WHERE user_id=? AND category=?
        """, (user_id, category))
        rows = cur.fetchall()
        return [dict(row) for row in rows]

    def total_expenses(self, user_id):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT SUM(amount) as total FROM expenses WHERE user_id=?",
            (user_id,)
        )
        row = cur.fetchone()
        return row["total"] if row["total"] else 0

    def get_savings(self, user_id):
        return self.get_income(user_id) - self.total_expenses(user_id)

    def category_summary(self, user_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE user_id=?
            GROUP BY category
            ORDER BY total DESC;
        """, (user_id,))
        return [dict(row) for row in cur.fetchall()]

    def monthly_summary(self, user_id, year, month):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT SUM(amount) as total
            FROM expenses
            WHERE user_id=?
            AND strftime('%Y', date)=?
            AND strftime('%m', date)=?;  
        """, (user_id, str(year), f"{month:02d}"))

        row = cur.fetchone()
        return row["total"] if row["total"] else 0

    def clear_expenses(self, user_id):
        cur = self.conn.cursor()
        cur.execute(
            "DELETE FROM expenses WHERE user_id=?",
            (user_id,)
        )
        self.conn.commit()

    # ---------- CLEANUP ----------
    def __del__(self):
        self.conn.close()
