"""Authentication API integration tests."""
import pytest
import json
from models import User, db


@pytest.mark.integration
@pytest.mark.auth
class TestAuthRegistration:
    """User registration API tests."""
    
    def test_register_success(self, client, db_session, create_verification_code):
        """Test successful registration."""
        email = 'newuser@example.com'
        # Create verification code
        verification_code_obj = create_verification_code(email=email, code='123456')
        
        data = {
            'username': 'newuser',
            'email': email,
            'password': 'testpass123',
            'verification_code': verification_code_obj.code
        }
        
        response = client.post('/api/auth/register', json=data)
        
        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data['message'] == 'User registered successfully'
        assert 'data' in json_data
        assert 'user' in json_data['data']
        assert 'tokens' in json_data['data']
        assert json_data['data']['user']['username'] == 'newuser'
        assert json_data['data']['user']['email'] == email
        assert json_data['data']['user']['role'] == 'user'
    
    def test_register_duplicate_email(self, client, test_user, create_verification_code):
        """Test duplicate email registration."""
        # Create verification code (even though email exists, we still need it for schema validation)
        verification_code_obj = create_verification_code(email=test_user.email, code='123456')
        
        data = {
            'username': 'diffuser',  # Max 12 characters per schema validation
            'email': test_user.email,  # Use existing email
            'password': 'testpass123',
            'verification_code': verification_code_obj.code
        }
        
        response = client.post('/api/auth/register', json=data)
        
        assert response.status_code == 409
        json_data = response.get_json()
        assert json_data['error'] == 'email_exists'
    
    def test_register_duplicate_username(self, client, test_user, create_verification_code):
        """Test duplicate username registration."""
        email = 'different@example.com'
        # Create verification code
        verification_code_obj = create_verification_code(email=email, code='123456')
        
        data = {
            'username': test_user.username,  # Use existing username
            'email': email,
            'password': 'testpass123',
            'verification_code': verification_code_obj.code
        }
        
        response = client.post('/api/auth/register', json=data)
        
        assert response.status_code == 409
        json_data = response.get_json()
        assert json_data['error'] == 'username_exists'
    
    def test_register_invalid_email(self, client):
        """Test invalid email registration."""
        data = {
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'testpass123'
        }
        
        response = client.post('/api/auth/register', json=data)
        
        assert response.status_code == 400
        json_data = response.get_json()
        assert json_data['error'] == 'validation_error'
    
    def test_register_short_password(self, client):
        """Test short password registration."""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': '123'  # Too short
        }
        
        response = client.post('/api/auth/register', json=data)
        
        assert response.status_code == 400
        json_data = response.get_json()
        assert json_data['error'] == 'validation_error'


@pytest.mark.integration
@pytest.mark.auth
class TestAuthLogin:
    """User login API tests."""
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        data = {
            'email': test_user.email,
            'password': 'testpass123'
        }
        
        response = client.post('/api/auth/login', json=data)
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['message'] == 'Login successful'
        assert 'tokens' in json_data['data']
        assert 'access_token' in json_data['data']['tokens']
        assert 'refresh_token' in json_data['data']['tokens']
    
    def test_login_invalid_email(self, client, db_session):
        """Test invalid email login."""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        }
        
        response = client.post('/api/auth/login', json=data)
        
        assert response.status_code == 401
        json_data = response.get_json()
        assert json_data['error'] == 'invalid_credentials'
    
    def test_login_wrong_password(self, client, test_user):
        """Test wrong password login."""
        data = {
            'email': test_user.email,
            'password': 'wrongpassword'
        }
        
        response = client.post('/api/auth/login', json=data)
        
        assert response.status_code == 401
        json_data = response.get_json()
        assert json_data['error'] == 'invalid_credentials'
    
    def test_login_disabled_user(self, client, db_session, user_factory):
        """Test disabled user login."""
        disabled_user = user_factory(is_active=False)
        
        data = {
            'email': disabled_user.email,
            'password': 'testpass123'
        }
        
        response = client.post('/api/auth/login', json=data)
        
        assert response.status_code == 403
        json_data = response.get_json()
        assert json_data['error'] == 'account_disabled'


@pytest.mark.integration
@pytest.mark.auth
class TestAuthProfile:
    """User profile API tests."""
    
    def test_get_profile_success(self, client, auth_headers, test_user):
        """Test get user profile."""
        response = client.get('/api/auth/profile', headers=auth_headers)
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['message'] == 'Profile retrieved successfully'
        assert json_data['data']['user']['id'] == test_user.id
        assert json_data['data']['user']['username'] == test_user.username
    
    def test_get_profile_unauthorized(self, client):
        """Test unauthorized profile access."""
        response = client.get('/api/auth/profile')
        
        assert response.status_code == 401
    
    def test_update_profile_username(self, client, auth_headers, test_user, db_session):
        """Test update username."""
        data = {'username': 'updateduser'}  # Max 12 characters per schema validation
        
        response = client.put('/api/auth/profile', json=data, headers=auth_headers)
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['data']['user']['username'] == 'updateduser'
        
        # Verify database was updated
        db_session.refresh(test_user)
        assert test_user.username == 'updateduser'
    
    def test_update_profile_email(self, client, auth_headers, test_user, db_session, create_verification_code):
        """Test update email."""
        new_email = 'newemail@example.com'
        # Create verification code for the new email
        verification_code_obj = create_verification_code(email=new_email, code='123456')
        
        data = {
            'email': new_email,
            'verification_code': verification_code_obj.code
        }
        
        response = client.put('/api/auth/profile', json=data, headers=auth_headers)
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['data']['user']['email'] == new_email
    
    def test_update_profile_password(self, client, auth_headers, test_user, db_session):
        """Test update password."""
        old_hash = test_user.password_hash
        data = {'password': 'newpassword123'}
        
        response = client.put('/api/auth/profile', json=data, headers=auth_headers)
        
        assert response.status_code == 200
        
        # Verify password was updated
        db_session.refresh(test_user)
        assert test_user.password_hash != old_hash
        assert test_user.check_password('newpassword123') is True
    
    def test_update_profile_duplicate_username(self, client, auth_headers, test_user, user_factory):
        """Test update to existing username."""
        other_user = user_factory()
        data = {'username': other_user.username}
        
        response = client.put('/api/auth/profile', json=data, headers=auth_headers)
        
        assert response.status_code == 409
        json_data = response.get_json()
        assert json_data['error'] == 'username_exists'


@pytest.mark.integration
@pytest.mark.auth
class TestAuthRefresh:
    """Token refresh API tests."""
    
    def test_refresh_token_success(self, app, client, test_user):
        """Test successful token refresh."""
        with app.app_context():
            from utils.auth import create_tokens
            tokens = create_tokens(test_user)
            refresh_token = tokens['refresh_token']
        
        headers = {'Authorization': f'Bearer {refresh_token}'}
        response = client.post('/api/auth/refresh', headers=headers)
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert 'access_token' in json_data['data']
        assert json_data['data']['token_type'] == 'Bearer'
    
    def test_refresh_token_invalid(self, client):
        """Test invalid refresh token."""
        headers = {'Authorization': 'Bearer invalid_token'}
        response = client.post('/api/auth/refresh', headers=headers)
        
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.auth
class TestAuthLogout:
    """User logout API tests."""
    
    def test_logout_success(self, client, auth_headers):
        """Test successful logout."""
        response = client.post('/api/auth/logout', headers=auth_headers)
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['message'] == 'Logout successful'
    
    def test_logout_unauthorized(self, client):
        """Test unauthorized logout."""
        response = client.post('/api/auth/logout')
        
        assert response.status_code == 401

