from flask import Flask, render_template, request, redirect, url_for, session, flash
from database.db import get_db, init_db, seed_db, get_user_profile, get_user_summary, get_user_transactions, get_user_category_totals, get_expense_by_id, update_expense
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


@app.route("/analytics")
def analytics():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login', error="Please log in to access this page"))

    return render_template("analytics.html")


@app.route("/profile")
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login', error="Please log in to access this page"))

    # Get date filters from query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    conn = get_db()
    try:
        # User profile data
        user_row = get_user_profile(conn, user_id)
        user = {
            "name": user_row['name'],
            "email": user_row['email'],
            "created_at": user_row['created_at']
        }

        # Filtered data retrieval
        stats = get_user_summary(conn, user_id, start_date, end_date)

        transactions = [dict(row) for row in get_user_transactions(conn, user_id, start_date, end_date)]

        category_totals = get_user_category_totals(conn, user_id, start_date, end_date)
        total_spent = stats['total_spent']
        category_breakdown = [
            {
                "category": row['category'],
                "amount": row['total'],
                "percentage": round((row['total'] / total_spent * 100), 1) if total_spent > 0 else 0.0
            }
            for row in category_totals
        ]

        return render_template("profile.html",
                               user=user,
                               stats=stats,
                               transactions=transactions,
                               category_breakdown=category_breakdown,
                               start_date=start_date,
                               end_date=end_date)
    finally:
        conn.close()



from datetime import date as py_date

@app.route("/expenses/add")
def add_expense():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login', error="Please log in to add an expense"))
    return render_template("add_expense.html", today=py_date.today().isoformat())



@app.route("/expenses/add", methods=["POST"])
def add_expense_post():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login', error="Please log in to add an expense"))

    # Get form data
    amount_str = request.form.get('amount', '').strip()
    category = request.form.get('category', '').strip()
    date = request.form.get('date', '').strip()
    description = request.form.get('description', '').strip()

    # Validation
    error = None
    if not amount_str or not category or not date:
        error = "Amount, category and date are required"
    elif date > py_date.today().isoformat():
        error = "Expense date cannot be in the future"
    else:
        try:
            amount = float(amount_str)
            if amount <= 0:
                error = "Amount must be a positive number"
        except ValueError:
            error = "Invalid amount format"


    if error:
        return render_template("add_expense.html", error=error), 400

    # Save to database
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, description)
        )
        conn.commit()
    except Exception as e:
        return render_template("add_expense.html", error="An error occurred while saving the expense"), 500
    finally:
        conn.close()

    return redirect(url_for('profile'))



@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login', error="Please log in to edit this expense"))

    conn = get_db()
    try:
        expense = get_expense_by_id(conn, id, user_id)
        if expense is None:
            return "Expense not found", 404

        return render_template("edit_expense.html",
                               expense=expense,
                               today=py_date.today().isoformat())
    finally:
        conn.close()

@app.route("/expenses/<int:id>/edit", methods=["POST"])
def edit_expense_post(id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login', error="Please log in to edit this expense"))

    # Get form data
    amount_str = request.form.get('amount', '').strip()
    category = request.form.get('category', '').strip()
    date = request.form.get('date', '').strip()
    description = request.form.get('description', '').strip()

    # Validation
    error = None
    if not amount_str or not category or not date:
        error = "Amount, category and date are required"
    elif date > py_date.today().isoformat():
        error = "Expense date cannot be in the future"
    else:
        try:
            amount = float(amount_str)
            if amount <= 0:
                error = "Amount must be a positive number"
        except ValueError:
            error = "Invalid amount format"

    if error:
        # We need the expense data to pre-populate the form again on error
        conn = get_db()
        try:
            expense = get_expense_by_id(conn, id, user_id)
            if expense is None:
                return "Expense not found", 404
            # Use submitted data if validation failed to prevent data loss
            expense_data = {
                "amount": amount_str,
                "category": category,
                "date": date,
                "description": description
            }
            return render_template("edit_expense.html",
                                   error=error,
                                   expense=expense_data,
                                   today=py_date.today().isoformat()), 400
        finally:
            conn.close()

    # Save to database
    conn = get_db()
    try:
        rows_affected = update_expense(conn, id, user_id, amount, category, date, description)
        if rows_affected == 0:
            return "Expense not found", 404
        conn.commit()
    except Exception as e:
        return render_template("edit_expense.html", error="An error occurred while updating the expense"), 500
    finally:
        conn.close()

    return redirect(url_for('profile'))



@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)