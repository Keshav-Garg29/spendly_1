import sqlite3
from database.db import get_db

# Test foreign key constraint enforcement
print("Testing foreign key constraint...")

conn = get_db()
try:
    # Try to insert expense with non-existent user_id (should fail)
    conn.execute('''
        INSERT INTO expenses (user_id, amount, category, date, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (999, 10.0, "Food", "2026-05-08", "Test expense"))
    conn.commit()
    print("ERROR: Foreign key constraint not enforced!")
except sqlite3.IntegrityError as e:
    print(f"SUCCESS: Foreign key constraint enforced - {e}")
finally:
    conn.close()