from database.db import get_db, init_db, seed_db

# Test that seed_db prevents duplicates
print("Testing seed duplicate prevention...")

# First call
seed_db()
conn = get_db()
cursor = conn.execute("SELECT COUNT(*) FROM expenses")
count1 = cursor.fetchone()[0]
conn.close()
print(f"After first seed: {count1} expenses")

# Second call
seed_db()
conn = get_db()
cursor = conn.execute("SELECT COUNT(*) FROM expenses")
count2 = cursor.fetchone()[0]
conn.close()
print(f"After second seed: {count2} expenses")

if count1 == count2:
    print("SUCCESS: No duplicates created on second seed call")
else:
    print(f"ERROR: Duplicate created! Count changed from {count1} to {count2}")