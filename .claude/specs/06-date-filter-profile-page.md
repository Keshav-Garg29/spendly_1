# Spec: Date Filter for Profile Page

## Overview
This feature introduces date filtering to the user's profile page. Currently, the profile page shows all-time statistics and transactions. Adding a date filter allows users to analyze their spending patterns over specific periods (e.g., a specific month or year), which is a critical step in making the expense tracker useful for budgeting and reporting.

## Depends on
- 05-backend-profile-routes

## Routes
- `GET /profile` — Modified to accept optional `start_date` and `end_date` query parameters. These parameters will be used to filter the user's summary, transactions, and category totals. Access level: logged-in.

## Database changes
No database changes. This feature utilizes existing columns in the `expenses` table (`date` column). Queries in `database/db.py` will be updated to include `WHERE date BETWEEN ? AND ?` clauses when date filters are provided.

## Templates
- **Modify:** `templates/profile.html`
    - Add a date filter form at the top of the profile content.
    - The form should include two date input fields (`start_date` and `end_date`) and a "Filter" button.
    - Add a "Clear Filter" link/button that appears only when a filter is active, resetting the view to all-time data.
    - Ensure the selected dates are preserved in the input fields after the page reloads.

## Files to change
- `app.py`
- `database/db.py`
- `templates/profile.html`

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Date formats must be consistent with the database (`YYYY-MM-DD`).

## Definition of done
- [ ] Users can enter a start date and end date on the profile page and click "Filter".
- [ ] The "Total Spent" and "Total Expenses" stats update to reflect only the filtered date range.
- [ ] The "Top Category" updates based on the filtered range.
- [ ] The "Category Breakdown" list and percentages are recalculated for the filtered range.
- [ ] The transaction table only displays expenses that fall within the selected date range.
- [ ] The "Clear Filter" button removes the date filters and restores all-time data.
- [ ] Invalid or empty date filters do not crash the application and default to showing all data.
