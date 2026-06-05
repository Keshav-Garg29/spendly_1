# Spec: Add Expense

## Overview
This feature allows authenticated users to record their daily expenses by providing an amount, category, date, and description. This is a core functionality of Spendly, transforming it from a view-only profile to an interactive expense tracker where users can manage their own data.

## Depends on
06-date-filter-profile-page

## Routes
- `GET /expenses/add` — Render the "Add Expense" form — logged-in
- `POST /expenses/add` — Process the form and save the expense to the database — logged-in

## Database changes
No database changes. The `expenses` table already contains the necessary columns: `user_id`, `amount`, `category`, `date`, and `description`.

## Templates
- **Create:** `templates/add_expense.html`
- **Modify:** `templates/profile.html` (add a link to the "Add Expense" page)

## Files to change
- `app.py`

## Files to create
- `templates/add_expense.html`
- `tests/test_07-add-expense.py`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`

## Definition of done
- [ ] `GET /expenses/add` renders a form with fields for amount, category, date, and description.
- [ ] `POST /expenses/add` validates that required fields are present and that the amount is a positive number.
- [ ] `POST /expenses/add` saves the expense to the database associated with the currently logged-in user.
- [ ] After successful submission, the user is redirected to the profile page.
- [ ] Invalid submissions show a clear error message to the user.
- [ ] All tests in `tests/test_07-add-expense.py` pass.
