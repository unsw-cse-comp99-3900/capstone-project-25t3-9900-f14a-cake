"""Database models package - unified export of all models and utilities."""
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# Create global instances
db = SQLAlchemy()
bcrypt = Bcrypt()

# Import all models (ensure imported after db and bcrypt initialization)
from .user import User
from .invoice import Invoice
from .verification_code import EmailVerificationCode

# Export all models and utilities, maintain backward compatibility
__all__ = ['User', 'Invoice', 'EmailVerificationCode', 'db', 'bcrypt']
