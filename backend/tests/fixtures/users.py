"""User test data fixtures."""
import pytest
from faker import Faker
from models import User, db

fake = Faker()


@pytest.fixture
def user_factory(db_session):
    """User factory function."""
    def _create_user(**kwargs):
        defaults = {
            'username': fake.user_name(),
            'email': fake.email(),
            'password': 'testpass123',
            'role': 'user',
            'is_active': True
        }
        defaults.update(kwargs)
        
        user = User(**defaults)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    return _create_user


@pytest.fixture
def multiple_users(user_factory):
    """Create multiple test users."""
    users = []
    for i in range(5):
        user = user_factory(
            username=f'testuser{i}',
            email=f'test{i}@example.com'
        )
        users.append(user)
    return users

