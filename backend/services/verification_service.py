"""Email verification code service"""
from datetime import datetime, timedelta
from models import db, EmailVerificationCode
from services.email_service import send_verification_email
import config


def generate_and_send_code(email, mailgun_domain, mailgun_api_key, from_email):
    """
    Generate a verification code and send it via email
    
    Args:
        email: User email address
        mailgun_domain: Mailgun domain
        mailgun_api_key: Mailgun API key
        from_email: From email address
    
    Returns:
        (success: bool, message: str, code_obj: EmailVerificationCode or None)
    """
    try:
        # Check if there's a recent code (within 60 seconds)
        recent_code = EmailVerificationCode.query.filter(
            EmailVerificationCode.email == email,
            EmailVerificationCode.created_at > datetime.utcnow() - timedelta(seconds=60),
            EmailVerificationCode.is_invalidated == False
        ).order_by(EmailVerificationCode.created_at.desc()).first()
        
        if recent_code:
            return False, "Please wait 60 seconds before requesting a new code", None
        
        # Invalidate all existing codes for this email
        existing_codes = EmailVerificationCode.query.filter(
            EmailVerificationCode.email == email,
            EmailVerificationCode.is_invalidated == False,
            EmailVerificationCode.is_used == False
        ).all()
        
        for code in existing_codes:
            code.invalidate()
        
        # Create new verification code
        verification_code = EmailVerificationCode(email=email)
        db.session.add(verification_code)
        db.session.commit()
        
        # Send email with verification code
        success, message, response_data = send_verification_email(
            recipient_email=email,
            verification_code=verification_code.code,
            mailgun_domain=mailgun_domain,
            mailgun_api_key=mailgun_api_key,
            from_email=from_email
        )
        
        if success:
            return True, "Verification code sent successfully", verification_code
        else:
            # If email sending fails, delete the code
            db.session.delete(verification_code)
            db.session.commit()
            return False, message, None
            
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to generate verification code: {str(e)}", None


def verify_code(email, code):
    """
    Verify a verification code
    
    Args:
        email: User email address
        code: Verification code to verify
    
    Returns:
        (success: bool, message: str, code_obj: EmailVerificationCode or None)
    """
    try:
        # Find the most recent valid code for this email
        verification_code = EmailVerificationCode.query.filter(
            EmailVerificationCode.email == email,
            EmailVerificationCode.code == code,
            EmailVerificationCode.is_used == False,
            EmailVerificationCode.is_invalidated == False
        ).order_by(EmailVerificationCode.created_at.desc()).first()
        
        if not verification_code:
            return False, "Invalid verification code", None
        
        if not verification_code.is_valid():
            return False, "Verification code has expired", None
        
        # Mark code as used
        verification_code.mark_as_used()
        db.session.commit()
        
        return True, "Verification code verified successfully", verification_code
        
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to verify code: {str(e)}", None

