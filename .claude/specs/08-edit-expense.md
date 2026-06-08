# Spec: Edit Expense

## Overview
The Edit Expense feature allows users to modify the details of an existing expense. This provides a critical way for users to correct errors in their spending records, such as updating the amount, category, date, or description of a transaction.

## Depends on
- 01 Database Setup
- 07 Add Expense

## Routes
- `GET /expenses/<int:id>/edit` — Render the edit form with current expense details — logged-in
- `POST /expenses/<int:id>/edit` — Process the updated expense data and save to database — logged-in

## Database changes
No database changes.

## Templates
- **Create:** `templates/edit_expense.html` — Pre-populated form for updating expense details.
- **Modify:** No templates modified.

## Files to change
- `app.py` — Implement GET and POST handlers for editing expenses.
- `database/db.py` — Add helper functions to retrieve a single expense and update it.

## Files to create
- `templates/edit_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- **Ownership Verification:** The application must verify that the expense being edited belongs to the currently logged-in user. If the expense does not exist or belongs to another user, return a 404 Not Found.

## Definition of done
- [ ] Unauthenticated users are redirected to login when accessing `/expenses/<id>/edit`.
- [ ] Users cannot edit expenses belonging to other users (returns 404).
- [ ] The edit form is pre-populated with the existing values of the expense.
- [ ] Validations are enforced:
    - Amount must be a positive number.
    - Date cannot be in the future.
    - Category and Date are required.
- [ ] Successful submission updates the database and redirects to the profile page.
- [ ] Input errors are displayed on the edit page without losing the other form data.
