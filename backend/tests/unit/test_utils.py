"""Utility function unit tests."""
import pytest
from utils.helpers import (
    validate_user_input,
    create_response,
    paginate_query,
    get_current_user
)
from models import User, db, Invoice
from flask import Flask


@pytest.mark.unit
class TestInputValidation:
    """Input validation tests."""
    
    def test_validate_user_input_required_fields(self):
        """Test required field validation."""
        data = {'email': 'test@example.com'}
        errors = validate_user_input(data, required_fields=['username', 'email'])
        
        assert 'username is required' in errors
        assert 'email is required' not in errors
    
    def test_validate_user_input_email_format(self):
        """Test email format validation."""
        # Valid email
        data = {'email': 'test@example.com'}
        errors = validate_user_input(data)
        assert 'Invalid email format' not in errors
        
        # Invalid email
        data = {'email': 'invalid-email'}
        errors = validate_user_input(data)
        assert 'Invalid email format' in errors
    
    def test_validate_user_input_username_format(self):
        """Test username format validation."""
        # Valid username
        data = {'username': 'testuser123'}
        errors = validate_user_input(data)
        assert len([e for e in errors if 'Username' in e]) == 0
        
        # Too short
        data = {'username': 'ab'}
        errors = validate_user_input(data)
        assert any('at least 3 characters' in e for e in errors)
        
        # Contains invalid characters
        data = {'username': 'test user!'}
        errors = validate_user_input(data)
        assert any('only contain letters' in e for e in errors)
    
    def test_validate_user_input_password_length(self):
        """Test password length validation."""
        # Too short
        data = {'password': '12345'}
        errors = validate_user_input(data)
        assert any('at least 6 characters' in e for e in errors)
        
        # Valid
        data = {'password': '123456'}
        errors = validate_user_input(data)
        assert len([e for e in errors if 'Password' in e]) == 0


@pytest.mark.unit
class TestResponseHelpers:
    """Response helper function tests."""
    
    def test_create_response_success(self, app):
        """Test success response."""
        with app.app_context():
            response, status_code = create_response('Success', data={'key': 'value'})
            
            assert status_code == 200
            json_data = response.get_json()
            assert json_data['message'] == 'Success'
            assert json_data['data'] == {'key': 'value'}
            assert 'error' not in json_data
    
    def test_create_response_error(self, app):
        """Test error response."""
        with app.app_context():
            response, status_code = create_response(
                'Error occurred',
                error='validation_error',
                status_code=400
            )
            
            assert status_code == 400
            json_data = response.get_json()
            assert json_data['message'] == 'Error occurred'
            assert json_data['error'] == 'validation_error'


@pytest.mark.unit
class TestPagination:
    """Pagination function tests."""
    
    def test_paginate_query(self, db_session, test_user, invoice_factory):
        """Test pagination query."""
        # Create 15 invoices
        for _ in range(15):
            invoice_factory(user_id=test_user.id)
        
        query = db_session.query(Invoice).filter_by(user_id=test_user.id)
        result = paginate_query(query, page=1, per_page=10)
        
        assert 'items' in result
        assert 'pagination' in result
        assert len(result['items']) == 10
        assert result['pagination']['total'] == 15
        assert result['pagination']['pages'] == 2
        assert result['pagination']['has_next'] is True
        assert result['pagination']['has_prev'] is False
    
    def test_paginate_query_max_per_page(self, db_session, test_user, invoice_factory):
        """Test maximum per page limit."""
        for _ in range(5):
            invoice_factory(user_id=test_user.id)
        
        query = db_session.query(Invoice).filter_by(user_id=test_user.id)
        # Request per_page exceeding maximum
        result = paginate_query(query, page=1, per_page=200, max_per_page=100)
        
        assert len(result['items']) == 5  # Only 5 items actually
        # per_page should be limited to 100
        assert result['pagination']['per_page'] <= 100

