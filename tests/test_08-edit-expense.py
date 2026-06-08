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
    """A test client that is already logged in as 'testuser'."""
    client.post('/register', data={
        'name': 'Test User',
        'email': 'testuser@example.com',
        'password': 'testpass123',
        'confirm_password': 'testpass123'
    })
    client.post('/login', data={
        'email': 'testuser@example.com',
        'password': 'testpass123'
    })
    return client

@pytest.fixture
def other_user_client(client):
    """A separate logged-in user to test ownership boundaries."""
    client.post('/register', data={
        'name': 'Other User',
        'email': 'other@example.com',
        'password': 'otherpass123',
        'confirm_password': 'otherpass123'
    })
    client.post('/login', data={
        'email': 'other@example.com',
        'password': 'otherpass123'
    })
    return client

@pytest.fixture
def expense_setup(auth_client, app):
    """Creates a sample expense for the authenticated user."""
    with app.app_context():
        conn = get_db()
        # Use session to get current user_id
        # Since auth_client is used, we can just query the user by email
        user = conn.execute("SELECT id FROM users WHERE email = ?", ('testuser@example.com',)).fetchone()
        user_id = user['id']

        cursor = conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, 50.0, "Food", "2026-01-01", "Initial Meal")
        )
        conn.commit()
        expense_id = cursor.lastrowid
        return expense_id

class TestEditExpenseAuth:
    def test_get_edit_unauthenticated_redirects(self, client):
        response = client.get('/expenses/1/edit')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_post_edit_unauthenticated_redirects(self, client):
        response = client.post('/expenses/1/edit', data={'amount': '10.0'})
        assert response.status_code == 302
        assert '/login' in response.location

class TestEditExpenseOwnership:
    def test_get_edit_not_owned_returns_404(self, auth_client, other_user_client, expense_setup):
        # Attempt to access testuser's expense using other_user_client
        response = other_user_client.get(f'/expenses/{expense_setup}/edit')
        assert response.status_code == 404
        assert b'Expense not found' in response.data

    def test_post_edit_not_owned_returns_404(self, other_user_client, expense_setup):
        # Attempt to update testuser's expense using other_user_client
        response = other_user_client.post(f'/expenses/{expense_setup}/edit', data={
            'amount': '100.0',
            'category': 'Hacking',
            'date': '2026-01-01',
            'description': 'Unauthorized change'
        })
        assert response.status_code == 404
        assert b'Expense not found' in response.data

    def test_get_edit_non_existent_returns_404(self, auth_client):
        response = auth_client.get('/expenses/99999/edit')
        assert response.status_code == 404
        assert b'Expense not found' in response.data

class TestEditExpenseHappyPath:
    def test_get_edit_success(self, auth_client, expense_setup):
        response = auth_client.get(f'/expenses/{expense_setup}/edit')
        assert response.status_code == 200
        assert b'Initial Meal' in response.data
        assert b'50.0' in response.data
        assert b'Food' in response.data

    def test_post_edit_success_and_redirect(self, auth_client, expense_setup):
        updated_data = {
            'amount': '75.50',
            'category': 'Dining',
            'date': '2026-01-02',
            'description': 'Updated Meal'
        }
        response = auth_client.post(f'/expenses/{expense_setup}/edit', data=updated_data)
        assert response.status_code == 302
        assert '/profile' in response.location

    def test_post_edit_db_side_effect(self, auth_client, app, expense_setup):
        updated_data = {
            'amount': '75.50',
            'category': 'Dining',
            'date': '2026-01-02',
            'description': 'Updated Meal'
        }
        auth_client.post(f'/expenses/{expense_setup}/edit', data=updated_data)

        with app.app_context():
            conn = get_db()
            expense = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_setup,)).fetchone()
            assert expense['amount'] == 75.50
            assert expense['category'] == 'Dining'
            assert expense['date'] == '2026-01-02'
            assert expense['description'] == 'Updated Meal'

class TestEditExpenseValidation:
    @pytest.mark.parametrize("payload, expected_error", [
        ({'amount': '', 'category': 'Food', 'date': '2026-01-01'}, "Amount, category and date are required"),
        ({'amount': '10.0', 'category': '', 'date': '2026-01-01'}, "Amount, category and date are required"),
        ({'amount': '10.0', 'category': 'Food', 'date': ''}, "Amount, category and date are required"),
        ({'amount': 'abc', 'category': 'Food', 'date': '2026-01-01'}, "Invalid amount format"),
        ({'amount': '-5.0', 'category': 'Food', 'date': '2026-01-01'}, "Amount must be a positive number"),
        ({'amount': '0', 'category': 'Food', 'date': '2026-01-01'}, "Amount must be a positive number"),
    ])
    def test_post_edit_invalid_inputs(self, auth_client, expense_setup, payload, expected_error):
        response = auth_client.post(f'/expenses/{expense_setup}/edit', data=payload)
        assert response.status_code == 400
        assert expected_error.encode() in response.data

    def test_post_edit_future_date(self, auth_client, expense_setup):
        future_date = (date.today() + timedelta(days=1)).isoformat()
        response = auth_client.post(f'/expenses/{expense_setup}/edit', data={
            'amount': '10.0',
            'category': 'Food',
            'date': future_date,
            'description': 'Future'
        })
        assert response.status_code == 400
        assert b"Expense date cannot be in the future" in response.data

    def test_post_edit_data_persistence_on_error(self, auth_client, expense_setup):
        """Verify that submitted data is preserved in the form after a validation error."""
        submitted_data = {
            'amount': '-10.0', # Trigger error
            'category': 'New Category',
            'date': '2026-01-05',
            'description': 'Updated Description'
        }
        response = auth_client.post(f'/expenses/{expense_setup}/edit', data=submitted_data)

        assert response.status_code == 400
        # The form should contain the SUBMITTED values, not the ORIGINAL DB values
        assert b'New Category' in response.data
        assert b'Updated Description' in response.data
        assert b'-10.0' in response.data
        assert b'2026-01-05' in response.data
