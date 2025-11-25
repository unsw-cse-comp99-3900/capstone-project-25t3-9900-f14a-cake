"""Authentication-related data validation schemas."""
from marshmallow import Schema, fields, validate, ValidationError, validates
import re


class RegisterSchema(Schema):
    """Schema for user registration."""
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=80),
        error_messages={'required': 'Username is required'}
    )
    email = fields.Email(
        required=True,
        error_messages={'required': 'Email is required', 'invalid': 'Invalid email format'}
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=6, max=128),
        error_messages={'required': 'Password is required'}
    )
    verification_code = fields.Str(
        required=True,
        validate=validate.Length(equal=6),
        error_messages={'required': 'Verification code is required', 'invalid': 'Verification code must be 6 digits'}
    )
    role = fields.Str(
        missing='user',
        validate=validate.OneOf(['user', 'admin']),
        error_messages={'invalid': 'Role must be either "user" or "admin"'}
    )
    
    @validates('username')
    def validate_username(self, value: str) -> None:
        """
        Validate username format.
        
        Args:
            value: Username string to validate
        
        Raises:
            ValidationError: If username format is invalid
        """
        if not value.replace('_', '').replace('-', '').isalnum():
            raise ValidationError('Username can only contain letters, numbers, underscores and hyphens')
        if len(value) > 12:
            raise ValidationError('Username must be 20 characters or less.')
    @validates('verification_code')
    def validate_verification_code(self, value: str) -> None:
        """
        Validate verification code format.
        
        Args:
            value: Verification code string to validate
        
        Raises:
            ValidationError: If verification code format is invalid
        """
        if not value or not value.isdigit() or len(value) != 6:
            raise ValidationError('Verification code must be 6 digits')


class LoginSchema(Schema):
    """Schema for user login."""
    email = fields.Email(
        required=True,
        error_messages={'required': 'Email is required', 'invalid': 'Invalid email format'}
    )
    password = fields.Str(
        required=True,
        error_messages={'required': 'Password is required'}
    )


class UpdateProfileSchema(Schema):
    """Schema for updating user profile."""
    username = fields.Str(
        validate=validate.Length(min=3, max=80),
        allow_none=True
    )
    email = fields.Email(
        allow_none=True,
        error_messages={'invalid': 'Invalid email format'}
    )
    password = fields.Str(
        validate=validate.Length(min=6, max=128),
        allow_none=True
    )
    verification_code = fields.Str(
        validate=validate.Length(equal=6),
        allow_none=True,
        error_messages={'invalid': 'Verification code must be 6 digits'}
    )
    
    @validates('username')
    def validate_username(self, value: str) -> None:
        """
        Validate username format.
        
        Username must contain only alphanumeric characters, underscores, and hyphens.
        Maximum length is 12 characters.
        
        Args:
            value: Username string to validate (can be None)
        
        Raises:
            ValidationError: If username format is invalid
        """
        if value and not value.replace('_', '').replace('-', '').isalnum():
            raise ValidationError('Username can only contain letters, numbers, underscores and hyphens')
        if len(value) > 12:
            raise ValidationError('Username must be 20 characters or less.')
    @validates('verification_code')
    def validate_verification_code(self, value: str) -> None:
        """
        Validate verification code format.
        
        Verification code must be exactly 6 digits.
        
        Args:
            value: Verification code string to validate (can be None)
        
        Raises:
            ValidationError: If verification code format is invalid
        """
        if value and (not value.isdigit() or len(value) != 6):
            raise ValidationError('Verification code must be 6 digits')


class ResetPasswordSchema(Schema):
    """Schema for resetting password."""
    email = fields.Email(
        required=True,
        error_messages={'required': 'Email is required', 'invalid': 'Invalid email format'}
    )
    verification_code = fields.Str(
        required=True,
        validate=validate.Length(equal=6),
        error_messages={'required': 'Verification code is required', 'invalid': 'Verification code must be 6 digits'}
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=6, max=128),
        error_messages={'required': 'Password is required'}
    )
    
    @validates('verification_code')
    def validate_verification_code(self, value: str) -> None:
        """
        Validate verification code format.
        
        Args:
            value: Verification code string to validate
        
        Raises:
            ValidationError: If verification code format is invalid
        """
        if not value or not value.isdigit() or len(value) != 6:
            raise ValidationError('Verification code must be 6 digits')

