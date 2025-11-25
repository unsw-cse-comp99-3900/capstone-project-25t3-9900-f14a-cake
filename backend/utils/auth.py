"""JWT authentication utility functions."""
import os
from functools import wraps
from flask import current_app, jsonify
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token, create_refresh_token,
    get_jwt_identity, get_jwt
)
from datetime import timedelta

class AuthManager:
    """Authentication manager for JWT configuration."""
    
    def __init__(self, app=None):
        self.jwt = JWTManager()
        if app:
            self.init_app(app)
    
    def init_app(self, app) -> None:
        """
        Initialize JWT configuration.
        
        Args:
            app: Flask application instance
        """
        # JWT configuration
        app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600)))
        app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(seconds=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000)))
        
        # Disable blacklist feature for now (requires storage mechanism like Redis)
        # If blacklist is needed, implement token_revoked_loader callback
        app.config['JWT_BLACKLIST_ENABLED'] = False
        
        # Disable CSRF protection (usually not needed for API services)
        app.config['JWT_COOKIE_CSRF_PROTECT'] = False
        app.config['JWT_CSRF_CHECK_FORM'] = False
        
        self.jwt.init_app(app)
        
        # Configure JWT error handlers
        self._configure_error_handlers()
    
    def _configure_error_handlers(self) -> None:
        """Configure JWT error handlers."""
        
        @self.jwt.expired_token_loader
        def expired_token_callback(jwt_header, jwt_payload):
            return jsonify({
                'message': 'Token has expired',
                'error': 'token_expired'
            }), 401
        
        @self.jwt.invalid_token_loader
        def invalid_token_callback(error):
            # Add error details for debugging
            current_app.logger.error(f'Invalid token error: {str(error)}')
            return jsonify({
                'message': 'Invalid token',
                'error': 'invalid_token',
                'details': str(error) if current_app.debug else None
            }), 401
        
        @self.jwt.unauthorized_loader
        def missing_token_callback(error):
            return jsonify({
                'message': 'Authorization token is required',
                'error': 'authorization_required'
            }), 401
        
        @self.jwt.needs_fresh_token_loader
        def token_not_fresh_callback(jwt_header, jwt_payload):
            return jsonify({
                'message': 'Fresh token required',
                'error': 'fresh_token_required'
            }), 401
        
        @self.jwt.revoked_token_loader
        def revoked_token_callback(jwt_header, jwt_payload):
            return jsonify({
                'message': 'Token has been revoked',
                'error': 'token_revoked'
            }), 401

def role_required(*allowed_roles):
    """
    Role-based permission decorator - requires JWT authentication and role check.
    
    Args:
        *allowed_roles: Variable number of allowed role names
    
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            # Get current user information (JWT identity is string)
            current_user_id = get_jwt_identity()
            
            # Get user role from JWT payload
            jwt_data = get_jwt()
            user_role = jwt_data.get('role', 'user')
            is_active = jwt_data.get('is_active', True)
            
            # Check if user is disabled
            if not is_active:
                return jsonify({
                    'message': 'Account is disabled',
                    'error': 'account_disabled'
                }), 403
            
            # Check role permissions
            if user_role not in allowed_roles:
                return jsonify({
                    'message': 'Insufficient permissions',
                    'error': 'insufficient_permissions',
                    'required_roles': list(allowed_roles),
                    'user_role': user_role
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Admin permission decorator."""
    return role_required('admin')(f)

def create_tokens(user):
    """
    Create JWT tokens for user.
    
    Args:
        user: User object
    
    Returns:
        Dictionary with access_token, refresh_token, token_type, and expires_in
    """
    # JWT identity must be string type
    user_id_str = str(user.id)
    
    access_token = create_access_token(
        identity=user_id_str,
        additional_claims={
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'is_active': user.is_active
        }
    )
    
    refresh_token = create_refresh_token(identity=user_id_str)
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()
    }
