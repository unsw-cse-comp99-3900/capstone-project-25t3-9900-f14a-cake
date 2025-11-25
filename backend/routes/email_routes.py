"""Email sending routes."""
from flask import Blueprint, request, jsonify, current_app, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.email_service import send_invoice_email
from services.invoice_service import get_invoice_by_id
from utils.helpers import create_response
from typing import Tuple
import os
import config
import re
import tempfile

email_bp = Blueprint('email', __name__)


def is_valid_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address string
    
    Returns:
        True if email format is valid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


@email_bp.route('/send-email', methods=['POST'])
@jwt_required()
def handle_send_email() -> Tuple[Response, int]:
    """
    Send XML invoice to specified email address.
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    # Initialize temp_file_path at the start to avoid UnboundLocalError
    temp_file_path = None
    
    try:
        data = request.get_json()
        
        if not data:
            return create_response(
                'No data provided',
                error='validation_error',
                status_code=400
            )
        
        email = data.get('email', '').strip()
        xml_filename = data.get('xml_filename')
        invoice_id = data.get('invoice_id')
        
        if not email:
            return create_response(
                'Email is required',
                error='validation_error',
                status_code=400
            )
        
        # Validate email format
        if not is_valid_email(email):
            return create_response(
                'Invalid email format. Please enter a valid email address (e.g., user@example.com)',
                error='validation_error',
                status_code=400
            )
        
        xml_path = None
        
        # Try to get XML from file system first
        if xml_filename:
            xml_path = os.path.join(current_app.config['UPLOAD_FOLDER'], xml_filename)
            if os.path.exists(xml_path):
                # File exists, use it
                pass
            else:
                # File doesn't exist, try to get from database if invoice_id is provided
                xml_path = None
        
        # If file doesn't exist and invoice_id is provided, try to get XML from database
        if not xml_path and invoice_id:
            user_id = int(get_jwt_identity())
            invoice = get_invoice_by_id(invoice_id, user_id)
            
            if invoice and invoice.xml_content:
                # Create a temporary file with XML content from database
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False)
                temp_file.write(invoice.xml_content)
                temp_file.close()
                temp_file_path = temp_file.name
                xml_path = temp_file_path
                current_app.logger.info(f"Using XML from database for invoice {invoice_id}")
            else:
                return create_response(
                    'XML content not found in database. Please regenerate the XML.',
                    error='file_not_found',
                    status_code=404
                )
        elif not xml_path:
            # No file and no invoice_id, return error
            return create_response(
                'XML file not found. The file has been deleted (files are auto-deleted after 30 minutes). Please go back and regenerate the XML.',
                error='file_not_found',
                status_code=404
            )
        
        # Check Mailgun configuration
        if not all([config.MAILGUN_DOMAIN, config.MAILGUN_API_KEY]):
            return create_response(
                'Email service not configured. Mailgun credentials are missing. Please contact the administrator.',
                error='configuration_error',
                status_code=500
            )
        
        # Send email
        success, message, response_data = send_invoice_email(
            xml_filepath=xml_path,
            recipient_email=email,
            mailgun_domain=config.MAILGUN_DOMAIN,
            mailgun_api_key=config.MAILGUN_API_KEY,
            from_email=config.MAILGUN_FROM_EMAIL
        )
        
        if success:
            return create_response(
                message,
                data={'mailgun_response': response_data},
                status_code=200
            )
        else:
            # Return appropriate HTTP status based on status code
            status_code = response_data.get('status_code', 500) if response_data else 500
            
            return create_response(
                message,
                error='email_send_failed',
                status_code=status_code
            )
        
    except Exception as e:
        current_app.logger.error(f"Error sending email: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(
            'Email sending failed',
            error='server_error',
            status_code=500
        )
    finally:
        # Clean up temporary file if created
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                current_app.logger.warning(f"Failed to delete temporary file {temp_file_path}: {str(e)}")
