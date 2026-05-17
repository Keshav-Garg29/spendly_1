import sys
import os
import random
import datetime
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import get_db

def parse_arguments():
    """Parse and validate command line arguments."""
    if len(sys.argv) != 4:
        print("Usage: /seed-expenses <user_id> <count> <months>")
        print("Example: /seed-expenses 1 50 6")
        sys.exit(1)

    try:
        user_id = int(sys.argv[1])
        count = int(sys.argv[2])
        months = int(sys.argv[3])
    except ValueError:
        print("Usage: /seed-expenses <user_id> <count> <months>")
        print("Example: /seed-expenses 1 50 6")
        sys.exit(1)

    if user_id <= 0 or count <= 0 or months <= 0:
        print("Error: All arguments must be positive integers")
        sys.exit(1)

    return user_id, count, months

def verify_user_exists(user_id):
    """Check if the user exists in the database."""
    conn = get_db()
    try:
        cursor = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if cursor.fetchone() is None:
            print(f"No user found with id {user_id}.")
            sys.exit(1)
    finally:
        conn.close()

def get_date_range(months):
    """Get the date range for the past 'months' months."""
    end_date = datetime.date.today()
    start_date = end_date - timedelta(days=30 * months)
    return start_date, end_date

def random_date(start_date, end_date):
    """Generate a random date between start_date and end_date."""
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return start_date + timedelta(days=random_days)

def get_category_weights():
    """Return category weights for distribution (Food most common, Health/Entertainment least)."""
    return {
        "Food": 30,
        "Transport": 20,
        "Bills": 15,
        "Shopping": 15,
        "Other": 10,
        "Health": 5,
        "Entertainment": 5
    }

def get_category_details():
    """Return category details with amount ranges and sample descriptions."""
    return {
        "Food": {
            "amount_range": (50, 800),
            "descriptions": [
                "Lunch at restaurant", "Dinner with friends", "Groceries from supermarket",
                "Breakfast at cafe", "Snacks and beverages", "Food delivery order",
                "Vegetables and fruits", "Milk and dairy products", "Rice and lentils",
                "Cooking oil and spices"
            ]
        },
        "Transport": {
            "amount_range": (20, 500),
            "descriptions": [
                "Auto rickshaw fare", "Bus ticket", "Metro recharge", "Fuel for bike",
                "Car parking fee", "Cab/Ola/Uber ride", "Train ticket", "Bike maintenance",
                "Toll charges", "Vehicle service"
            ]
        },
        "Bills": {
            "amount_range": (200, 3000),
            "descriptions": [
                "Electricity bill", "Water bill", "Internet bill", "Mobile phone recharge",
                "Gas cylinder", "DTH/cable TV", "Maintenance charges", "Property tax",
                "Garbage collection", "Society maintenance"
            ]
        },
        "Health": {
            "amount_range": (100, 2000),
            "descriptions": [
                "Doctor consultation", "Medicines from pharmacy", "Medical test",
                "Dental checkup", "Eye checkup", "Vitamins and supplements",
                "First aid supplies", "Health checkup package", "Therapy session",
                "Fitness class"
            ]
        },
        "Entertainment": {
            "amount_range": (100, 1500),
            "descriptions": [
                "Movie tickets", "Concert/show tickets", "Amusement park",
                "Streaming subscription", "Gaming expenses", "Books and magazines",
                "Museum entry", "Sports event tickets", "Picnic supplies", "Hobby materials"
            ]
        },
        "Shopping": {
            "amount_range": (200, 5000),
            "descriptions": [
                "Clothing purchase", "Footwear", "Electronics accessory",
                "Home decor item", "Kitchen utensils", "Personal care products",
                "Gift for family", "Festival shopping", "Online shopping", "Jewelry"
            ]
        },
        "Other": {
            "amount_range": (50, 1000),
            "descriptions": [
                "Stationery items", "Postage and courier", "Bank charges",
                "ATM withdrawal fee", "Donation/charity", "Pet supplies",
                "Cleaning supplies", "Light bulbs", "Batteries", "Miscellaneous"
            ]
        }
    }

def select_category(weights):
    """Select a category based on weights."""
    categories = list(weights.keys())
    weights_list = list(weights.values())
    return random.choices(categories, weights=weights_list)[0]

def generate_expense(user_id, category_details, category, start_date, end_date):
    """Generate a single expense record."""
    details = category_details[category]
    amount_min, amount_max = details["amount_range"]
    amount = round(random.uniform(amount_min, amount_max), 2)
    expense_date = random_date(start_date, end_date)
    description = random.choice(details["descriptions"])

    return {
        "user_id": user_id,
        "amount": amount,
        "category": category,
        "date": expense_date.isoformat(),
        "description": description
    }

def main():
    # Parse arguments
    user_id, count, months = parse_arguments()

    # Verify user exists
    verify_user_exists(user_id)

    # Get date range
    start_date, end_date = get_date_range(months)

    # Get category details and weights
    category_details = get_category_details()
    weights = get_category_weights()

    # Generate expenses
    expenses = []
    for _ in range(count):
        category = select_category(weights)
        expense = generate_expense(user_id, category_details, category, start_date, end_date)
        expenses.append(expense)

    # Insert expenses in a single transaction
    conn = get_db()
    try:
        conn.execute("BEGIN TRANSACTION")

        cursor = conn.executemany('''
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
        ''', [(e["user_id"], e["amount"], e["category"], e["date"], e["description"]) for e in expenses])

        conn.commit()
        inserted_count = cursor.rowcount

        # Get date range of inserted expenses
        if inserted_count > 0:
            cursor = conn.execute('''
                SELECT MIN(date) as min_date, MAX(date) as max_date
                FROM expenses
                WHERE user_id = ? AND date >= ? AND date <= ?
            ''', (user_id, start_date.isoformat(), end_date.isoformat()))
            date_range = cursor.fetchone()

            # Get sample of 5 records
            cursor = conn.execute('''
                SELECT id, amount, category, date, description
                FROM expenses
                WHERE user_id = ? AND date >= ? AND date <= ?
                ORDER BY date DESC
                LIMIT 5
            ''', (user_id, start_date.isoformat(), end_date.isoformat()))
            sample_records = cursor.fetchall()
        else:
            date_range = None
            sample_records = []

    except Exception as e:
        conn.rollback()
        print(f"Error inserting expenses: {e}")
        sys.exit(1)
    finally:
        conn.close()

    # Print confirmation
    print(f"Inserted {inserted_count} expenses for user {user_id}")
    if date_range:
        print(f"Date range: {date_range['min_date']} to {date_range['max_date']}")
    else:
        print("Date range: No expenses inserted")

    print("\nSample of inserted records:")
    print("ID | Amount (Rs) | Category | Date | Description")
    print("-" * 80)
    for record in sample_records:
        print(f"{record['id']:2} | {record['amount']:8.2f} | {record['category']:12} | {record['date']:10} | {record['description']}")

if __name__ == "__main__":
    main()