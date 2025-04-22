import os
import tempfile
import pytest
from app import create_app, db
from app.models.user import User
from config import TestConfig


@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app(TestConfig)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Create the database and the database tables
    with app.app_context():
        db.create_all()
        # Create a test user
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
    
    yield app
    
    # Close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()


@pytest.fixture
def auth(client):
    """Authentication helper for tests."""
    class AuthActions:
        def login(self, username='testuser', password='password'):
            return client.post(
                '/login',
                data={'username': username, 'password': password},
                follow_redirects=True
            )
            
        def logout(self):
            return client.get('/logout', follow_redirects=True)
            
    return AuthActions()