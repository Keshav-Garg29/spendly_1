import sqlite3
from database.db import get_db

# Test row_factory setting
print("Testing row_factory...")

conn = get_db()
try:
    # Check if row_factory is set to sqlite3.Row
    if conn.row_factory == sqlite3.Row:
        print("SUCCESS: row_factory is set to sqlite3.Row")
    else:
        print(f"ERROR: row_factory is {conn.row_factory}, expected sqlite3.Row")

    # Test that we can access columns by name
    cursor = conn.execute("SELECT * FROM users LIMIT 1")
    row = cursor.fetchone()
    if row:
        # Try to access by column name
        email = row['email']
        print(f"SUCCESS: Can access column by name - email: {email}")
    else:
        print("ERROR: No rows found in users table")

finally:
    conn.close()