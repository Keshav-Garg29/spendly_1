from flask import Flask, render_template, request, redirect, url_for, session, flash
from database.db import get_db, init_db, seed_db
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "dev-secret-key-for-spendly"

# Initialize database on startup
with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    if session.get('user_id'):
        return redirect(url_for('profile'))
    return render_template("landing.html")


@app.route("/register")
def register():
    if session.get('user_id'):
        return redirect(url_for('profile'))
    error = request.args.get('error')
    success = request.args.get('success')
    return render_template("register.html", error=error, success=success)


@app.route("/register", methods=["POST"])
def register_post():
    # Get form data
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    # Validation
    error = None

    # Validate name
    if not name:
        error = "Name is required"
    elif len(name) > 100:
        error = "Name must be less than 100 characters"

    # Validate email
    if not error:
        if not email:
            error = "Email is required"
        elif '@' not in email or '.' not in email:
            error = "Please enter a valid email address"

    # Validate password
    if not error:
        if not password:
            error = "Password is required"
        elif len(password) < 8:
            error = "Password must be at least 8 characters long"
        elif password != confirm_password:
            error = "Passwords do not match"

    # If validation failed, show form again with error
    if error:
        return render_template("register.html", error=error), 400

    # Check if email already exists
    conn = get_db()
    try:
        cursor = conn.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone() is not None:
            error = "An account with this email already exists"
            return render_template("register.html", error=error), 400

        # Hash password and create user
        password_hash = generate_password_hash(password)
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash)
        )
        conn.commit()

        # Redirect to login with success message
        return redirect(url_for('login', success='Registration successful! Please log in.'))

    except sqlite3.IntegrityError as e:
        # Handle any database integrity errors (should be caught by email check above, but just in case)
        error = "An account with this email already exists"
        return render_template("register.html", error=error), 400
    except Exception as e:
        # Handle other unexpected errors
        error = "An error occurred during registration. Please try again."
        return render_template("register.html", error=error), 500
    finally:
        conn.close()


@app.route("/login", methods=["POST"])
def login_post():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    if not email or not password:
        return redirect(url_for('login', error="Email and password are required"))

    conn = get_db()
    try:
        cursor = conn.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            return redirect(url_for('profile'))
        else:
            return redirect(url_for('login', error="Invalid email or password"))
    finally:
        conn.close()


@app.route("/login")
def login():
    if session.get('user_id'):
        return redirect(url_for('profile'))
    error = request.args.get('error')
    success = request.args.get('success')
    return render_template("login.html", error=error, success=success)


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('landing'))


@app.route("/profile")
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login', error="Please log in to access this page"))

    # Hardcoded data for UI validation (Step 04)
    user = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "created_at": "2024-01-15"
    }
    stats = {
        "total_spent": 1420.00,
        "total_expenses": 42,
        "top_category": "Housing"
    }
    transactions = [
        {"date": "2024-05-20", "description": "Grocery Store", "category": "Food & Dining", "amount": -45.00},
        {"date": "2024-05-18", "description": "Monthly Rent", "category": "Housing", "amount": -1200.00},
        {"date": "2024-05-15", "description": "Gas Station", "category": "Transport", "amount": -60.00},
        {"date": "2024-05-12", "description": "Netflix", "category": "Entertainment", "amount": -40.00},
    ]
    category_breakdown = [
        {"category": "Housing", "amount": 1200, "percentage": 84.5},
        {"category": "Food & Dining", "amount": 120, "percentage": 8.5},
        {"category": "Transport", "amount": 60, "percentage": 4.2},
        {"category": "Entertainment", "amount": 40, "percentage": 2.8},
    ]

    return render_template("profile.html", user=user, stats=stats, transactions=transactions, category_breakdown=category_breakdown)



@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)