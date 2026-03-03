import sqlite3
from datetime import datetime

class ExpenseTracker:
    def __init__(self, db="expenses.db"):
        self.conn = sqlite3.connect(db, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.setup()


    # ---------- SETUP ----------
    def setup(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                notes TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value REAL
            );
        """)
        self.conn.commit()

    # ---------- INCOME ----------
    def update_income(self, new_income):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO settings (key, value)
            VALUES ('income', ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value;
        """, (new_income,))
        self.conn.commit()

    def get_income(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key='income'")
        row = cursor.fetchone()
        return row[0] if row else 0

    # ---------- EXPENSES ----------
    def add_expense(self, amount, category, notes=""):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO expenses (amount, category, notes)
            VALUES (?, ?, ?);
        """, (amount, category, notes))
        self.conn.commit()

    def delete_expense(self, exp_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id=?", (exp_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def edit_expense(self, exp_id, new_amount=None, new_category=None, new_notes=None):
        cursor = self.conn.cursor()
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
        params.append(exp_id)
        sql = f"UPDATE expenses SET {', '.join(updates)} WHERE id=?"
        cursor.execute(sql, params)
        self.conn.commit()
        return cursor.rowcount > 0

    def total_expenses(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT SUM(amount) FROM expenses;")
        total = cursor.fetchone()[0]
        return total if total else 0

    def get_savings(self):
        return self.get_income() - self.total_expenses()

    def get_expense_by_id(self, exp_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE id=?", (exp_id,))
        row = cursor.fetchone()
        if row:
            return {"id": row[0], "amount": row[1], "category": row[2],
                    "notes": row[3], "date": row[4]}
        return None

    def get_expenses(self, category=None):
        cursor = self.conn.cursor()
        if category:
            cursor.execute(
                "SELECT id, amount, category, notes FROM expenses WHERE category = ?",
                (category,)
            )
        else:
            cursor.execute(
                "SELECT id, amount, category, notes FROM expenses"
            )

        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "amount": row[1],
                "category": row[2],
                "notes": row[3]
            }
            for row in rows
        ]


    def category_summary(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT category, SUM(amount) as total
            FROM expenses
            GROUP BY category
            ORDER BY total DESC;
        """)
        return cursor.fetchall()

    def monthly_summary(self, year, month):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT SUM(amount)
            FROM expenses
            WHERE strftime('%Y', date)=? AND strftime('%m', date)=?;
        """, (str(year), f"{month:02d}"))
        row = cursor.fetchone()[0]
        return row if row else 0
    
    def clear_expenses(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM expenses;")
        self.conn.commit()

    # ---------- CLEANUP ----------
    def __del__(self):
        self.conn.close()


# ---------- CLI ----------
if __name__ == "__main__":
    tracker = ExpenseTracker()

    income = float(input("Enter your monthly income: "))
    tracker.update_income(income)
    print(f"Income set to {tracker.get_income()}")

    while True:
        print("\nExpense Tracker Menu:")
        print("1. Add Expense")
        print("2. Delete Expense")
        print("3. Edit Expense")
        print("4. View Total Expenses")
        print("5. View Savings")
        print("6. View Expense by Category")
        print("7. View Expense by ID")
        print("8. Category Summary")
        print("9. Monthly Summary")
        print("10. Exit")

        choice = input("Choose an option: ")

        if choice == '1':
            try:
                amount = float(input("Amount: "))
                category = input("Category: ")
                notes = input("Notes (optional): ")
                tracker.add_expense(amount, category, notes)
                print("Expense added.")
            except ValueError:
                print("Invalid amount.")

        elif choice == '2':
            exp_id = input("Enter expense ID to delete: ")
            if tracker.delete_expense(exp_id):
                print("Deleted.")
            else:
                print("Not found.")

        elif choice == '3':
            exp_id = input("Enter ID to edit: ")
            amount = input("New amount (blank to skip): ")
            category = input("New category (blank to skip): ")
            notes = input("New notes (blank to skip): ")
            amount = float(amount) if amount else None
            result = tracker.edit_expense(exp_id, amount, category or None, notes or None)
            print("Updated." if result else "Nothing changed.")

        elif choice == '4':
            print("Total spent:", tracker.total_expenses())

        elif choice == '5':
            print("Savings left:", tracker.get_savings())

        elif choice == '6':
            cat = input("Category: ")
            exps = tracker.get_expenses_by_category(cat)
            if not exps:
                print("No expenses in this category.")
            for e in exps:
                print(e)

        elif choice == '7':
            exp_id = input("Enter ID: ")
            e = tracker.get_expense_by_id(exp_id)
            print(e if e else "Not found.")

        elif choice == '8':
            print("\nCategory Summary:")
            for cat, total in tracker.category_summary():
                print(f"{cat}: {total}")

        elif choice == '9':
            y = int(input("Year (YYYY): "))
            m = int(input("Month (MM): "))
            print("Total for that month:", tracker.monthly_summary(y, m))

        elif choice == '10':
            print("Goodbye.")
            break

        else:
            print("Invalid choice.")
