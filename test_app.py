import pytest
from app import app, db, evaluate_password_strength, User
from flask import url_for

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_evaluate_password_strength():
    assert evaluate_password_strength('aA1!aaaa') == 'Strong'
    assert evaluate_password_strength('abc123') == 'Weak'
    assert evaluate_password_strength('Abc12345') == 'Medium'

def test_register_and_login(client):
    # Register a new user
    response = client.post('/register', data={
        'username': 'testuser',
        'password': 'Test@1234'
    }, follow_redirects=True)
    assert b'User registered successfully' in response.data

    # Login with the new user
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'Test@1234'
    }, follow_redirects=True)
    assert b'Welcome' in response.data

def test_password_update(client):
    # Setup: Register and log in
    client.post('/register', data={
        'username': 'testuser',
        'password': 'Test@1234'
    }, follow_redirects=True)
    client.post('/login', data={
        'username': 'testuser',
        'password': 'Test@1234'
    }, follow_redirects=True)

    # Update password
    response = client.post('/update-password', data={
        'new_password': 'New@Pass123'
    }, follow_redirects=True)
    assert b'Password updated.' in response.data

def test_set_webhook(client):
    # Setup: Register and log in
    client.post('/register', data={
        'username': 'testuser',
        'password': 'Test@1234'
    }, follow_redirects=True)
    client.post('/login', data={
        'username': 'testuser',
        'password': 'Test@1234'
    }, follow_redirects=True)

    # Set webhook
    response = client.post('/set-webhook', data={
        'webhook': 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'
    }, follow_redirects=True)
    assert b'Slack webhook URL updated.' in response.data