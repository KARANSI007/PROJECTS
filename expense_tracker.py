import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt

class ExpenseTracker:
    def __init__(self, db_name="expenses.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                amount REAL,
                                category TEXT,
                                date TEXT)''')
        self.conn.commit()

    def add_expense(self, amount, category):
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("INSERT INTO expenses (amount, category, date) VALUES (?, ?, ?)",
                            (amount, category, date))
        self.conn.commit()
        print(f"✅ Added: {amount} in {category}")

    def view_expenses(self):
        self.cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
        rows = self.cursor.fetchall()
        print("\n📒 Expense List:")
        for row in rows:
            print(f"ID:{row[0]} | {row[1]} INR | {row[2]} | {row[3]}")

    def monthly_report(self):
        self.cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
        data = self.cursor.fetchall()

        if not data:
            print("⚠️ No expenses recorded yet.")
            return

        categories = [row[0] for row in data]
        amounts = [row[1] for row in data]

        plt.pie(amounts, labels=categories, autopct="%1.1f%%")
        plt.title("Monthly Expense Breakdown")
        plt.show()

    def close(self):
        self.conn.close()


def main():
    tracker = ExpenseTracker()

    while True:
        print("\n📌 Expense Tracker Menu")
        print("1. Add Expense")
        print("2. View Expenses")
        print("3. Monthly Report")
        print("4. Exit")

        choice = input("Enter choice: ")

        if choice == "1":
            amount = float(input("Enter amount: "))
            category = input("Enter category (Food/Transport/Shopping/etc): ")
            tracker.add_expense(amount, category)

        elif choice == "2":
            tracker.view_expenses()

        elif choice == "3":
            tracker.monthly_report()

        elif choice == "4":
            tracker.close()
            print("👋 Exiting... Your data is saved in expenses.db")
            break

        else:
            print("❌ Invalid choice, try again.")


if __name__ == "__main__":
    main()
