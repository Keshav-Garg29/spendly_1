import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import get_db
from werkzeug.security import generate_password_hash
import random
import datetime

# Common Indian first names and last names
first_names = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan",
    "Krishna", "Ishaan", "Shaurya", "Atharv", "Naithik", "Veer", "Aadi",
    "Rohit", "Mohit", "Vikram", "Ankit", "Nikhil", "Rahul", "Priya", "Ananya",
    "Aanya", "Zoya", "Navya", "Anvi", "Diya", "Myra", "Kavya", "Charvi",
    "Saanvi", "Shanaya", "Kiara", "Sara", "Aalia", "Gauri", "Saisha", "Inaya"
]

last_names = [
    "Sharma", "Verma", "Patel", "Reddy", "Singh", "Kumar", "Das", "Kaur",
    "Gupta", "Agarwal", "Jain", "Shah", "Desai", "Malhotra", "Chatterjee",
    "Iyer", "Pillai", "Menon", "Gowda", "Kumar", "Rao", "Biswas", "Mishra",
    "Sinha", "Yadav", "Joshi", "Bhatt", "Kulkarni", "Nair", "Pradhan", "Chopra"
]

def generate_indian_user():
    """Generate a realistic Indian user with unique email."""
    while True:
        first = random.choice(first_names)
        last = random.choice(last_names)
        # Create email base: first.last (lowercase)
        email_base = f"{first.lower()}.{last.lower()}"
        # Add random 2-3 digit number
        num_suffix = random.randint(10, 999)
        email = f"{email_base}{num_suffix}@gmail.com"

        # Check if email exists in database
        conn = get_db()
        try:
            cursor = conn.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone() is None:
                # Email is unique
                break
        finally:
            conn.close()

    # Hash the password
    password_hash = generate_password_hash("password123")
    # Current timestamp for created_at (though table has default)
    created_at = datetime.datetime.now().isoformat()

    return {
        "name": f"{first} {last}",
        "email": email,
        "password_hash": password_hash,
        "created_at": created_at
    }

def main():
    user = generate_indian_user()

    # Insert into database
    conn = get_db()
    try:
        cursor = conn.execute('''
            INSERT INTO users (name, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
        ''', (user["name"], user["email"], user["password_hash"], user["created_at"]))
        user_id = cursor.lastrowid
        conn.commit()

        print(f"Inserted user:")
        print(f"  id: {user_id}")
        print(f"  name: {user['name']}")
        print(f"  email: {user['email']}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()