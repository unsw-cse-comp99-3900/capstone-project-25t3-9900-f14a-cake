"""User authentication related routes."""
from flask import Blueprint, request, jsonify, current_app, Response
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, get_jwt, create_access_token,
    create_refresh_token
)
from models import db, User
from schemas.auth_schema import RegisterSchema, LoginSchema, UpdateProfileSchema, ResetPasswordSchema
from utils.auth import create_tokens, role_required
from utils.helpers import get_current_user, create_response, validate_user_input, is_valid_email
from services.verification_service import generate_and_send_code, verify_code
from datetime import datetime
from typing import Tuple
import config

auth_bp = Blueprint('auth', __name__)

# Initialize Schema instances
register_schema = RegisterSchema()
login_schema = LoginSchema()
update_profile_schema = UpdateProfileSchema()
reset_password_schema = ResetPasswordSchema()


@auth_bp.route('/auth/send-verification-code', methods=['POST'])
def send_verification_code() -> Tuple[Response, int]:
    """
    Send email verification code.
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    try:
        data = request.get_json()
        
        if not data:
            return create_response(
                'No data provided',
                error='validation_error',
                status_code=400
            )
        
        email = data.get('email', '').strip()
        
        if not email:
            return create_response(
                'Email is required',
                error='validation_error',
                status_code=400
            )
        
        # Validate email format
        if not is_valid_email(email):
            return create_response(
                'Invalid email format',
                error='validation_error',
                status_code=400
            )
        
        # Check if email is already registered (but allow if it's the current user's email when updating profile)
        # This check is handled in the update_profile endpoint, so we allow sending code here
        # The update_profile endpoint will check if the email is already taken by another user
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            # Allow sending code if it's for profile update (we'll check ownership in update_profile)
            # For registration, this will be caught in the register endpoint
            pass
        
        # Check Mailgun configuration
        if not all([config.MAILGUN_DOMAIN, config.MAILGUN_API_KEY]):
            return create_response(
                'Email service not configured. Mailgun credentials are missing.',
                error='configuration_error',
                status_code=500
            )
        
        # Generate and send verification code
        success, message, code_obj = generate_and_send_code(
            email=email,
            mailgun_domain=config.MAILGUN_DOMAIN,
            mailgun_api_key=config.MAILGUN_API_KEY,
            from_email=config.MAILGUN_FROM_EMAIL
        )
        
        if success:
            return create_response(
                message,
                status_code=200
            )
        else:
            return create_response(
                message,
                error='verification_code_error',
                status_code=500
            )
        
    except Exception as e:
        current_app.logger.error(f'Send verification code error: {str(e)}')
        return create_response(
            'Failed to send verification code',
            error='server_error',
            status_code=500
        )


@auth_bp.route('/auth/verify-code', methods=['POST'])
def verify_verification_code() -> Tuple[Response, int]:
    """
    Verify email verification code.
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    try:
        data = request.get_json()
        
        if not data:
            return create_response(
                'No data provided',
                error='validation_error',
                status_code=400
            )
        
        email = data.get('email', '').strip()
        code = data.get('code', '').strip()
        
        if not email or not code:
            return create_response(
                'Email and verification code are required',
                error='validation_error',
                status_code=400
            )
        
        # Verify code
        success, message, code_obj = verify_code(email=email, code=code)
        
        if success:
            return create_response(
                message,
                status_code=200
            )
        else:
            return create_response(
                message,
                error='verification_failed',
                status_code=400
            )
        
    except Exception as e:
        current_app.logger.error(f'Verify code error: {str(e)}')
        return create_response(
            'Failed to verify code',
            error='server_error',
            status_code=500
        )


@auth_bp.route('/auth/register', methods=['POST'])
def register() -> Tuple[Response, int]:
    """
    User registration endpoint.
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    try:
        data = request.get_json()
        
        if not data:
            return create_response(
                'No data provided',
                error='validation_error',
                status_code=400
            )
        
        # Use Schema to validate data
        errors = register_schema.validate(data)
        if errors:
            return create_response(
                'Validation failed',
                data={'errors': errors},
                error='validation_error',
                status_code=400
            )
        
        # Verify email verification code
        verification_code = data.get('verification_code', '').strip()
        email = data.get('email', '').strip()
        
        if not verification_code:
            return create_response(
                'Verification code is required',
                error='validation_error',
                status_code=400
            )
        
        # Verify the code
        success, message, code_obj = verify_code(email=email, code=verification_code)
        
        if not success:
            return create_response(
                message,
                error='verification_failed',
                status_code=400
            )
        
        # Check if email already exists (double check)
        if User.query.filter_by(email=email).first():
            return create_response(
                'Email already registered',
                error='email_exists',
                status_code=409
            )
        
        # Check if username already exists
        if User.query.filter_by(username=data['username']).first():
            return create_response(
                'Username already taken',
                error='username_exists',
                status_code=409
            )
        
        # Create new user (default role is 'user' unless explicitly specified as admin and system allows)
        role = data.get('role', 'user')
        # Security consideration: registration does not allow direct creation of admin users
        if role == 'admin':
            role = 'user'
        
        new_user = User(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            role=role
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Generate JWT tokens
        tokens = create_tokens(new_user)
        
        return create_response(
            'User registered successfully',
            data={
                'user': new_user.to_dict(),
                'tokens': tokens
            },
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Registration error: {str(e)}')
        return create_response(
            'Registration failed',
            error='server_error',
            status_code=500
        )


@auth_bp.route('/auth/login', methods=['POST'])
def login() -> Tuple[Response, int]:
    """
    User login endpoint.
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    try:
        data = request.get_json()
        
        if not data:
            return create_response(
                'No data provided',
                error='validation_error',
                status_code=400
            )
        
        # Validate data using Schema
        errors = login_schema.validate(data)
        if errors:
            return create_response(
                'Validation failed',
                data={'errors': errors},
                error='validation_error',
                status_code=400
            )
        
        # Find user
        user = User.query.filter_by(email=data['email']).first()
        
        if not user:
            return create_response(
                'Invalid email or password',
                error='invalid_credentials',
                status_code=401
            )
        
        # Check if user is disabled
        if not user.is_active:
            return create_response(
                'Account is disabled',
                error='account_disabled',
                status_code=403
            )
        
        # Verify password
        if not user.check_password(data['password']):
            return create_response(
                'Invalid email or password',
                error='invalid_credentials',
                status_code=401
            )
        
        # Generate JWT tokens
        tokens = create_tokens(user)
        
        return create_response(
            'Login successful',
            data={
                'user': user.to_dict(),
                'tokens': tokens
            },
            status_code=200
        )
        
    except Exception as e:
        current_app.logger.error(f'Login error: {str(e)}')
        return create_response(
            'Login failed',
            error='server_error',
            status_code=500
        )


@auth_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout() -> Tuple[Response, int]:
    """
    User logout endpoint.
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    try:
        # Get JWT information
        jti = get_jwt()['jti']  # JWT ID
        
        # Note: Token blacklist mechanism needs to be implemented to truly invalidate tokens
        # Currently Flask-JWT-Extended's blacklist feature requires additional storage (e.g., Redis)
        # For simple implementation, client-side token deletion is sufficient
        
        return create_response(
            'Logout successful',
            status_code=200
        )
        
    except Exception as e:
        current_app.logger.error(f'Logout error: {str(e)}')
        return create_response(
            'Logout failed',
            error='server_error',
            status_code=500
        )


@auth_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh() -> Tuple[Response, int]:
    """
    Refresh access token endpoint.
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    try:
        user_id = get_jwt_identity()
        # JWT identity is string, convert to integer
        user = db.session.get(User, int(user_id))
        
        if not user:
            return create_response(
                'User not found',
                error='user_not_found',
                status_code=404
            )
        
        if not user.is_active:
            return create_response(
                'Account is disabled',
                error='account_disabled',
                status_code=403
            )
        
        # Generate new access token (identity must be string)
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_active': user.is_active
            }
        )
        
        return create_response(
            'Token refreshed successfully',
            data={
                'access_token': access_token,
                'token_type': 'Bearer',
                'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()
            },
            status_code=200
        )
        
    except Exception as e:
        current_app.logger.error(f'Token refresh error: {str(e)}')
        return create_response(
            'Token refresh failed',
            error='server_error',
            status_code=500
        )


@auth_bp.route('/auth/profile', methods=['GET'])
@jwt_required()
def get_profile() -> Tuple[Response, int]:
    """
    Get current user information endpoint.
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    try:
        user = get_current_user()
        
        if not user:
            return create_response(
                'User not found',
                error='user_not_found',
                status_code=404
            )
        
        return create_response(
            'Profile retrieved successfully',
            data={'user': user.to_dict()},
            status_code=200
        )
        
    except Exception as e:
        current_app.logger.error(f'Get profile error: {str(e)}')
        return create_response(
            'Failed to retrieve profile',
            error='server_error',
            status_code=500
        )


@auth_bp.route('/auth/profile', methods=['PUT'])
@jwt_required()
def update_profile() -> Tuple[Response, int]:
    """
    Update current user information endpoint.
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    try:
        user = get_current_user()
        
        if not user:
            return create_response(
                'User not found',
                error='user_not_found',
                status_code=404
            )
        
        data = request.get_json()
        
        if not data:
            return create_response(
                'No data provided',
                error='validation_error',
                status_code=400
            )
        
        # Validate data using Schema
        errors = update_profile_schema.validate(data)
        if errors:
            return create_response(
                'Validation failed',
                data={'errors': errors},
                error='validation_error',
                status_code=400
            )
        
        # Update username (if provided)
        if 'username' in data and data['username']:
            # Check if username is already taken by another user
            existing_user = User.query.filter(
                User.username == data['username'],
                User.id != user.id
            ).first()
            if existing_user:
                return create_response(
                    'Username already taken',
                    error='username_exists',
                    status_code=409
                )
            user.username = data['username']
        
        # Update email (if provided)
        if 'email' in data and data['email']:
            # Check if email was changed
            email_changed = data['email'] != user.email
            
            if email_changed:
                # If email was changed, verification code is required
                verification_code = data.get('verification_code', '').strip()
                if not verification_code:
                    return create_response(
                        'Verification code is required when changing email',
                        error='verification_code_required',
                        status_code=400
                    )
                
                # Verify verification code
                success, message, code_obj = verify_code(email=data['email'], code=verification_code)
                if not success:
                    return create_response(
                        message,
                        error='verification_failed',
                        status_code=400
                    )
            
            # Check if email is already registered by another user
            existing_user = User.query.filter(
                User.email == data['email'],
                User.id != user.id
            ).first()
            if existing_user:
                return create_response(
                    'Email already registered',
                    error='email_exists',
                    status_code=409
                )
            user.email = data['email']
        
        # Update password (if provided)
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return create_response(
            'Profile updated successfully',
            data={'user': user.to_dict()},
            status_code=200
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Update profile error: {str(e)}')
        return create_response(
            'Failed to update profile',
            error='server_error',
            status_code=500
        )


@auth_bp.route('/auth/reset-password', methods=['POST'])
def reset_password() -> Tuple[Response, int]:
    """
    Reset password endpoint.
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    """Reset password using email verification code"""
    try:
        data = request.get_json()
        
        if not data:
            return create_response(
                'No data provided',
                error='validation_error',
                status_code=400
            )
        
        # Use Schema to validate data
        errors = reset_password_schema.validate(data)
        if errors:
            return create_response(
                'Validation failed',
                data={'errors': errors},
                error='validation_error',
                status_code=400
            )
        
        email = data.get('email', '').strip()
        verification_code = data.get('verification_code', '').strip()
        new_password = data.get('password', '').strip()
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            # Don't reveal if email exists for security reasons
            return create_response(
                'Invalid email or verification code',
                error='invalid_credentials',
                status_code=400
            )
        
        # Verify the code
        success, message, code_obj = verify_code(email=email, code=verification_code)
        
        if not success:
            return create_response(
                'Invalid email or verification code',
                error='verification_failed',
                status_code=400
            )
        
        # Update password
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return create_response(
            'Password reset successfully',
            status_code=200
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Reset password error: {str(e)}')
        return create_response(
            'Failed to reset password',
            error='server_error',
            status_code=500
        )

