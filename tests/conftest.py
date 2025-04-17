import pytest
from app import app, db
from models import User

@pytest.fixture
def test_client():
    """Create a test client for the application."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

@pytest.fixture
def test_user():
    """Create a test user."""
    user = User(username='testuser')
    user.set_password('testpass')
    db.session.add(user)
    db.session.commit()
    return user 