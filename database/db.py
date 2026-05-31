import sqlite3
import os
from werkzeug.security import generate_password_hash

def get_db():
    """Returns a SQLite connection with row_factory and foreign keys enabled"""
    # Determine database file path - use project root
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'spendly.db')
    # Alternative: expense_tracker.db if spendly.db doesn't exist
    if not os.path.exists(db_path):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'expense_tracker.db')

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable dictionary-like row access
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
    return conn

def init_db():
    """Creates all tables using CREATE TABLE IF NOT EXISTS"""
    conn = get_db()
    try:
        # Create users table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        ''')

        # Create expenses table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        conn.commit()
    finally:
        conn.close()

def seed_db():
    """Inserts sample data for development, preventing duplicates"""
    conn = get_db()
    try:
        # Check if we already have users
        cursor = conn.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]

        if user_count > 0:
            # Data already seeded, return early
            return

        # Insert demo user
        demo_password_hash = generate_password_hash("demo123")
        cursor = conn.execute('''
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
        ''', ("Demo User", "demo@spendly.com", demo_password_hash))

        user_id = cursor.lastrowid

        # Sample expenses data - exactly 8 expenses with at least one per category
        sample_expenses = [
            # Food (1 expense)
            (user_id, 15.50, "Food", "2026-05-01", "Lunch at cafe"),

            # Transport (1 expense)
            (user_id, 45.00, "Transport", "2026-05-02", "Gas refill"),

            # Bills (2 expenses)
            (user_id, 85.00, "Bills", "2026-05-01", "Electricity bill"),
            (user_id, 45.00, "Bills", "2026-05-03", "Internet bill"),

            # Health (1 expense)
            (user_id, 30.00, "Health", "2026-05-04", "Pharmacy"),

            # Entertainment (1 expense)
            (user_id, 25.00, "Entertainment", "2026-05-06", "Movie tickets"),

            # Shopping (1 expense)
            (user_id, 60.00, "Shopping", "2026-05-02", "New shirt"),

            # Other (1 expense)
            (user_id, 20.00, "Other", "2026-05-07", "Gift for friend")
        ]

        # Insert sample expenses
        conn.executemany('''
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_expenses)

        conn.commit()
    finally:
        conn.close()

def get_user_profile(conn, user_id):
    """Fetches user name, email and creation date"""
    cursor = conn.execute("SELECT name, email, created_at FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()

def get_user_summary(conn, user_id):
    """Calculates total spent, total expenses count, and top category"""
    stats = {}

    # Total spent and count
    cursor = conn.execute("SELECT SUM(amount) as total, COUNT(*) as count FROM expenses WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    stats['total_spent'] = row['total'] if row['total'] else 0.0
    stats['total_expenses'] = row['count']

    # Top category
    cursor = conn.execute('''
        SELECT category FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY SUM(amount) DESC
        LIMIT 1
    ''', (user_id,))
    row = cursor.fetchone()
    stats['top_category'] = row['category'] if row else "None"

    return stats

def get_user_transactions(conn, user_id):
    """Fetches all expenses for the user, ordered by date descending"""
    cursor = conn.execute("SELECT date, description, category, amount FROM expenses WHERE user_id = ? ORDER BY date DESC", (user_id,))
    return cursor.fetchall()

def get_user_category_totals(conn, user_id):
    """Returns a list of categories and their total spent amounts"""
    cursor = conn.execute("SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ? GROUP BY category", (user_id,))
    return cursor.fetchall()
