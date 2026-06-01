import pytest
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
    client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'testpass123',
        'confirm_password': 'testpass123'
    })
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    return client

@pytest.fixture
def seed_expenses(app, auth_client):
    """Seeds specific expenses for date filtering tests."""
    with app.app_context():
        conn = get_db()
        user = conn.execute("SELECT id FROM users WHERE email = ?", ('test@example.com',)).fetchone()
        user_id = user['id']

        expenses = [
            (user_id, 100.0, "Food", "2026-01-01", "Expense A"),
            (user_id, 200.0, "Transport", "2026-06-01", "Expense B"),
            (user_id, 300.0, "Bills", "2026-12-01", "Expense C"),
        ]
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            expenses
        )
        conn.commit()
        conn.close()

class TestDateFilterProfile:
    def test_profile_auth_redirect(self, client):
        response = client.get('/profile')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_profile_no_filters(self, auth_client, seed_expenses):
        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert b'600.0' in response.data
        assert b'3' in response.data

    def test_profile_start_date_only(self, auth_client, seed_expenses):
        response = auth_client.get('/profile?start_date=2026-06-01')
        assert response.status_code == 200
        assert b'500.0' in response.data
        assert b'2' in response.data
        assert b'Expense B' in response.data
        assert b'Expense C' in response.data
        assert b'Expense A' not in response.data

    def test_profile_end_date_only(self, auth_client, seed_expenses):
        response = auth_client.get('/profile?end_date=2026-06-01')
        assert response.status_code == 200
        assert b'300.0' in response.data
        assert b'2' in response.data
        assert b'Expense A' in response.data
        assert b'Expense B' in response.data
        assert b'Expense C' not in response.data

    def test_profile_date_range(self, auth_client, seed_expenses):
        response = auth_client.get('/profile?start_date=2026-05-01&end_date=2026-07-01')
        assert response.status_code == 200
        assert b'200.0' in response.data
        assert b'1' in response.data
        assert b'Expense B' in response.data

    def test_profile_no_data_in_range(self, auth_client, seed_expenses):
        response = auth_client.get('/profile?start_date=2020-01-01&end_date=2020-01-01')
        assert response.status_code == 200
        assert b'0.0' in response.data
        assert b'0' in response.data
        assert b'None' in response.data

    def test_profile_filter_persistence(self, auth_client, seed_expenses):
        start, end = '2026-01-01', '2026-06-01'
        response = auth_client.get(f'/profile?start_date={start}&end_date={end}')
        assert response.status_code == 200
        assert f'value="{start}"'.encode() in response.data
        assert f'value="{end}"'.encode() in response.data

    def test_profile_invalid_dates(self, auth_client, seed_expenses):
        response_empty = auth_client.get('/profile?start_date=&end_date=')
        assert response_empty.status_code == 200
        assert b'600.0' in response_empty.data

        response_malformed = auth_client.get('/profile?start_date=not-a-date&end_date=!!!')
        assert response_malformed.status_code == 200
