import sqlite3
from database.db import get_db

# Test PRAGMA foreign_keys setting
print("Testing PRAGMA foreign_keys...")

conn = get_db()
try:
    # Check the foreign_keys setting
    cursor = conn.execute("PRAGMA foreign_keys")
    fk_setting = cursor.fetchone()[0]
    if fk_setting == 1:
        print("SUCCESS: PRAGMA foreign_keys is ON")
    else:
        print(f"ERROR: PRAGMA foreign_keys is {fk_setting}, expected 1")

finally:
    conn.close()