import pytest
from datetime import date, timedelta
from app import app as flask_app
from database.db import init_db, get_db

@pytest.fixture
def app():
    flask_app.config.update({
        'TESTING': True,
        'DATABASE': ':memory:',
        'SECRET_KEY': 'test-secret',
        'WTF_CSRF_ENABLED': False,
    })
    with flask_app.app_context():
        init_db()
        yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client):
    """A test client that is already logged in."""
    # Register a user
    client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'testpassword123',
        'confirm_password': 'testpassword123'
    })
    # Log in
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpassword123'
    })
    return client

class TestAddExpense:
    # --- Auth Guards ---

    def test_add_expense_page_guest_redirects(self, client):
        response = client.get('/expenses/add')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_add_expense_post_guest_redirects(self, client):
        response = client.post('/expenses/add', data={
            'amount': '10.00',
            'category': 'Food',
            'date': date.today().isoformat(),
            'description': 'Lunch'
        })
        assert response.status_code == 302
        assert '/login' in response.location

    # --- Happy Path ---

    def test_add_expense_page_renders_correctly(self, auth_client):
        response = auth_client.get('/expenses/add')
        assert response.status_code == 200
        assert b'amount' in response.data.lower()
        assert b'category' in response.data.lower()
        assert b'date' in response.data.lower()
        assert b'description' in response.data.lower()

    def test_add_expense_valid_submission_redirects_to_profile(self, auth_client):
        data = {
            'amount': '25.50',
            'category': 'Shopping',
            'date': date.today().isoformat(),
            'description': 'New book'
        }
        response = auth_client.post('/expenses/add', data=data)
        assert response.status_code == 302
        assert '/profile' in response.location

    def test_add_expense_valid_submission_saves_to_db(self, auth_client, app):
        # Set up data
        amount = 15.75
        category = 'Transport'
        expense_date = date.today().isoformat()
        description = 'Bus ticket'

        auth_client.post('/expenses/add', data={
            'amount': str(amount),
            'category': category,
            'date': expense_date,
            'description': description
        })

        # Verify DB side effect
        with app.app_context():
            conn = get_db()
            # Get the logged in user's id
            user_id = auth_client.session.get('user_id')
            cursor = conn.execute(
                "SELECT amount, category, date, description, user_id FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                (user_id,)
            )
            row = cursor.fetchone()

            assert row is not None, "Expense record should exist in database"
            assert row['amount'] == amount, f"Expected amount {amount}, got {row['amount']}"
            assert isinstance(row['amount'], float), "Amount should be stored as a float"
            assert row['category'] == category
            assert row['date'] == expense_date
            assert row['description'] == description
            assert row['user_id'] == user_id

    # --- Validation Errors ---

    @pytest.mark.parametrize("missing_field", ['amount', 'category', 'date'])
    def test_add_expense_missing_required_fields(self, auth_client, missing_field):
        data = {
            'amount': '10.00',
            'category': 'Food',
            'date': date.today().isoformat(),
            'description': 'Lunch'
        }
        del data[missing_field]

        response = auth_client.post('/expenses/add', data=data)
        assert response.status_code == 400
        assert b"Amount, category and date are required" in response.data

    def test_add_expense_invalid_amount_format(self, auth_client):
        data = {
            'amount': 'not-a-number',
            'category': 'Food',
            'date': date.today().isoformat(),
            'description': 'Lunch'
        }
        response = auth_client.post('/expenses/add', data=data)
        assert response.status_code == 400
        assert b"Invalid amount format" in response.data

    @pytest.mark.parametrize("bad_amount", ['0', '-10.50'])
    def test_add_expense_non_positive_amount(self, auth_client, bad_amount):
        data = {
            'amount': bad_amount,
            'category': 'Food',
            'date': date.today().isoformat(),
            'description': 'Lunch'
        }
        response = auth_client.post('/expenses/add', data=data)
        assert response.status_code == 400
        assert b"Amount must be a positive number" in response.data

    def test_add_expense_future_date(self, auth_client):
        future_date = (date.today() + timedelta(days=1)).isoformat()
        data = {
            'amount': '10.00',
            'category': 'Food',
            'date': future_date,
            'description': 'Lunch'
        }
        response = auth_client.post('/expenses/add', data=data)
        assert response.status_code == 400
        assert b"Expense date cannot be in the future" in response.data
