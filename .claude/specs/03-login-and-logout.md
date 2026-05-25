---
# Spec: Login and Logout

## Overview
This feature allows users to authenticate using their email and password, and subsequently sign out. It's the core of the app's security, ensuring that user data (expenses) is protected and only accessible to the authenticated owner.

## Depends on
- 01-Database Setup
- 02-Registration

## Routes
- `GET /login` — Display login form — public
- `POST /login` — Authenticate user and start session — public
- `GET /logout` — End session and redirect to landing — logged-in

## Database changes
No database changes.

## Templates
- **Modify:** `templates/login.html` — Ensure form is correct and handles errors/success
- **Modify:** `templates/base.html` — Add conditional navigation links based on auth status: Login/Register vs Profile/Logout

## Files to change
- `app.py`
- `templates/login.html`
- `templates/base.html`

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
- Use Flask's `session` for user state management.

## Definition of done
- [ ] User can log in with valid credentials and is redirected to the profile page.
- [ ] User sees an error message when providing invalid credentials.
- [ ] User is redirected to the landing page after logging out.
- [ ] Navigation bar updates to show "Profile" and "Logout" when logged in, and "Login" and "Register" when logged out.
- [ ] Attempting to access `/profile` while logged out redirects to `/login`.
---
