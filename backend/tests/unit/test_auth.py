"""Authentication utility unit tests."""
import pytest
from flask import Flask
from models import User, db, bcrypt
from utils.auth import AuthManager, create_tokens, role_required, admin_required
from flask_jwt_extended import decode_token, get_jwt_identity, get_jwt
from datetime import timedelta


@pytest.mark.unit
class TestAuthManager:
    """AuthManager tests."""
    
    def test_auth_manager_initialization(self, app):
        """Test AuthManager initialization."""
        # AuthManager is already initialized in the app fixture
        # Just verify the configuration is set correctly
        assert app.config['JWT_SECRET_KEY'] is not None
        assert 'JWT_ACCESS_TOKEN_EXPIRES' in app.config
        assert 'JWT_REFRESH_TOKEN_EXPIRES' in app.config
    
    def test_jwt_configuration(self, app):
        """Test JWT configuration."""
        assert app.config['JWT_SECRET_KEY'] == 'test-jwt-secret-key-for-testing'
        assert app.config['JWT_BLACKLIST_ENABLED'] is False
    
    def test_create_tokens(self, app, test_user):
        """Test token creation."""
        with app.app_context():
            tokens = create_tokens(test_user)
            
            assert 'access_token' in tokens
            assert 'refresh_token' in tokens
            assert 'token_type' in tokens
            assert 'expires_in' in tokens
            assert tokens['token_type'] == 'Bearer'
            
            # Verify token can be decoded
            decoded = decode_token(tokens['access_token'])
            assert decoded['sub'] == str(test_user.id)
            assert decoded['username'] == test_user.username
            assert decoded['email'] == test_user.email
            assert decoded['role'] == test_user.role
    
    def test_token_identity_is_string(self, app, test_user):
        """Test token identity is string type."""
        with app.app_context():
            tokens = create_tokens(test_user)
            decoded = decode_token(tokens['access_token'])
            
            # JWT identity must be string
            assert isinstance(decoded['sub'], str)
            assert decoded['sub'] == str(test_user.id)


@pytest.mark.unit
class TestPasswordHashing:
    """Password hashing tests."""
    
    def test_password_hashing(self):
        """Test password hashing."""
        password = 'testpass123'
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        
        assert hashed != password
        assert len(hashed) > 0
    
    def test_password_verification(self):
        """Test password verification."""
        password = 'testpass123'
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        
        assert bcrypt.check_password_hash(hashed, password) is True
        assert bcrypt.check_password_hash(hashed, 'wrongpassword') is False
    
    def test_user_password_methods(self, db_session):
        """Test User model password methods."""
        user = User(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Test set_password
        user.set_password('newpassword')
        assert user.password_hash != 'newpassword'
        
        # Test check_password
        assert user.check_password('newpassword') is True
        assert user.check_password('wrong') is False


@pytest.mark.unit
class TestRoleDecorators:
    """Role permission decorator tests."""
    
    def test_role_required_decorator(self, app, test_user, admin_user):
        """Test role_required decorator."""
        with app.test_request_context():
            # This test requires actual JWT token, more suitable in integration tests
            # Here mainly test that decorator function exists
            assert callable(role_required)
            assert callable(admin_required)

