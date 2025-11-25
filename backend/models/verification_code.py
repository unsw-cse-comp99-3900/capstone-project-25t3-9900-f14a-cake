"""Email verification code model"""
from datetime import datetime, timedelta
from . import db
import secrets
import string


class EmailVerificationCode(db.Model):
    """Email verification code model"""
    __tablename__ = 'email_verification_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    is_invalidated = db.Column(db.Boolean, default=False, nullable=False)
    
    def __init__(self, email):
        self.email = email
        self.code = self.generate_code()
        self.expires_at = datetime.utcnow() + timedelta(minutes=2)  # 2 minutes validity
        self.is_used = False
        self.is_invalidated = False
    
    @staticmethod
    def generate_code():
        """Generate a 6-digit verification code"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    def is_valid(self):
        """Check if the code is still valid"""
        if self.is_used or self.is_invalidated:
            return False
        if datetime.utcnow() > self.expires_at:
            return False
        return True
    
    def invalidate(self):
        """Invalidate this code (when a new one is generated)"""
        self.is_invalidated = True
    
    def mark_as_used(self):
        """Mark this code as used"""
        self.is_used = True
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_used': self.is_used,
            'is_invalidated': self.is_invalidated
        }
    
    def __repr__(self):
        return f'<EmailVerificationCode {self.email}: {self.code}>'

