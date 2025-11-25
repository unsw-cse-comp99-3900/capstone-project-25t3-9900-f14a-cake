"""Authentication utility functions."""
from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, verify_jwt_in_request
)
from models import User, db
import re

def token_required(f):
    """JWT token verification decorator."""
    return jwt_required()(f)

def get_current_user():
    """
    Get current authenticated user.
    
    Returns:
        User object or None if not authenticated
    """
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        # JWT identity is string, convert to integer
        return db.session.get(User, int(user_id))
    except:
        return None

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_user_input(data, required_fields=None, optional_fields=None):
    """
    Validate user input data.
    
    Args:
        data: Input data dictionary
        required_fields: List of required field names
        optional_fields: List of optional field names
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    if not isinstance(data, dict):
        errors.append('Invalid data format')
        return errors
    
    # Validate required fields
    if required_fields:
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f'{field} is required')
    
    # Validate email format
    if 'email' in data and data['email']:
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            errors.append('Invalid email format')
    
    # Validate username format
    if 'username' in data and data['username']:
        username = data['username']
        if len(username) < 3:
            errors.append('Username must be at least 3 characters long')
        if len(username) > 80:
            errors.append('Username must be less than 80 characters')
        if not username.replace('_', '').replace('-', '').isalnum():
            errors.append('Username can only contain letters, numbers, underscores and hyphens')
    
    # Validate password
    if 'password' in data and data['password']:
        password = data['password']
        if len(password) < 6:
            errors.append('Password must be at least 6 characters long')
        if len(password) > 128:
            errors.append('Password must be less than 128 characters')
    
    return errors

def create_response(message: str, data=None, status_code: int = 200, error: str = None):
    """
    Create unified response format.
    
    Args:
        message: Response message
        data: Optional response data
        status_code: HTTP status code
        error: Optional error code
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    response = {'message': message}
    
    if data is not None:
        response['data'] = data
    
    if error:
        response['error'] = error
    
    return jsonify(response), status_code

def paginate_query(query, page: int = 1, per_page: int = 10, max_per_page: int = 100) -> dict:
    """
    Pagination query helper function.
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        per_page: Items per page
        max_per_page: Maximum items per page
    
    Returns:
        Dictionary with 'items' and 'pagination' keys
    """
    try:
        page = max(1, int(page))
        per_page = min(max_per_page, max(1, int(per_page)))
        
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return {
            'items': [item.to_dict() for item in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next,
                'prev_num': pagination.prev_num,
                'next_num': pagination.next_num
            }
        }
    except Exception as e:
        current_app.logger.error(f'Pagination error: {str(e)}')
        return {
            'items': [],
            'pagination': {
                'page': 1,
                'per_page': per_page,
                'total': 0,
                'pages': 0,
                'has_prev': False,
                'has_next': False,
                'prev_num': None,
                'next_num': None
            }
        }
