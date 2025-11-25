"""OCR related routes."""
from flask import Blueprint, request, jsonify, current_app, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.ocr_service import process_ocr, extract_invoice_fields
from services.invoice_service import create_invoice_from_ocr
from utils import allowed_file
from utils.helpers import create_response
from typing import Tuple
import config
import requests

ocr_bp = Blueprint('ocr', __name__)


@ocr_bp.route('/ocr', methods=['POST'])
@jwt_required()
def handle_ocr() -> Tuple[Response, int]:
    """
    Process uploaded file and perform OCR recognition via Veryfi API.
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    try:
        # Check file upload
        if 'file' not in request.files:
            return create_response(
                'No file provided',
                error='validation_error',
                status_code=400
            )
        
        file = request.files['file']
        
        if file.filename == '':
            return create_response(
                'No file selected',
                error='validation_error',
                status_code=400
            )
        
        # Check file type
        if not allowed_file(file.filename, config.ALLOWED_EXTENSIONS):
            file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'unknown'
            allowed_exts = ', '.join(sorted(config.ALLOWED_EXTENSIONS))
            return create_response(
                f'File type "{file_ext}" is not supported. Please upload a {allowed_exts.upper()} file.',
                error='validation_error',
                status_code=400
            )
        
        # Check file size (before reading)
        file.seek(0, 2)  # Move to end of file
        file_size = file.tell()  # Get file size (bytes)
        file.seek(0)  # Reset to beginning
        
        file_size_mb = file_size / (1024 * 1024)
        if file_size_mb > config.MAX_FILE_SIZE_MB:
            return create_response(
                f'File size is {file_size_mb:.2f}MB, which exceeds the {config.MAX_FILE_SIZE_MB}MB limit. Please upload a smaller file.',
                error='file_too_large',
                status_code=400
            )
        
        # Check credentials
        if not config.VERYFI_CLIENT_ID or not config.VERYFI_AUTHORIZATION:
            print("ERROR: Veryfi credentials missing!")
            print(f"  CLIENT_ID: {'OK' if config.VERYFI_CLIENT_ID else 'MISSING'}")
            print(f"  AUTHORIZATION: {'OK' if config.VERYFI_AUTHORIZATION else 'MISSING'}")
            return create_response(
                'Veryfi API credentials are not configured',
                error='configuration_error',
                status_code=500
            )
        
        # Call OCR service
        ocr_data, result_filename = process_ocr(
            file,
            config.VERYFI_CLIENT_ID,
            config.VERYFI_AUTHORIZATION,
            current_app.config['UPLOAD_FOLDER']
        )
        
        # Extract key fields
        extracted_data = extract_invoice_fields(ocr_data)
        
        # Get current user ID
        user_id = int(get_jwt_identity())
        
        # Save invoice record to database
        invoice = create_invoice_from_ocr(
            user_id=user_id,
            original_filename=file.filename,
            ocr_data=ocr_data,
            json_filename=result_filename
        )
        
        import time
        
        return create_response(
            'Document processed successfully',
            data={
            'raw_data': ocr_data,
            'extracted': extracted_data,
            'json_filename': result_filename,
                'invoice_id': invoice.id,
                'file_created_at': int(time.time())
            },
            status_code=200
        )
        
    except ValueError as e:
        # Document type error
        current_app.logger.error(f"Document type validation failed: {str(e)}")
        return create_response(
            'Invalid document type',
            error='validation_error',
            status_code=400
        )
    except requests.Timeout:
        current_app.logger.error("Request timeout")
        return create_response(
            'Request timeout. Please try again.',
            error='timeout_error',
            status_code=504
        )
    except Exception as e:
        current_app.logger.error(f"OCR processing error: {str(e)}")
        
        # Check if this is a Veryfi API error with status code
        if hasattr(e, 'veryfi_error') and e.veryfi_error and hasattr(e, 'status_code'):
            veryfi_status = e.status_code
            error_message = str(e)
            
            # Map Veryfi API status codes to error types and messages
            veryfi_error_mapping = {
                400: {'error': 'veryfi_error', 'message': "Couldn't download file from provided url."},
                403: {'error': 'veryfi_auth_error', 'message': 'Authentication credentials were not provided.'},
                404: {'error': 'veryfi_error', 'message': 'Not found.'},
                413: {'error': 'file_too_large', 'message': 'Request body too large.'},
                429: {'error': 'rate_limit_error', 'message': 'You have been rate limited. Please try again later.'},
                499: {'error': 'connection_error', 'message': 'Client closed request or lost connection. Please try again.'},
                500: {'error': 'veryfi_server_error', 'message': 'Unexpected error from OCR service. Please try again later.'},
                503: {'error': 'service_unavailable', 'message': 'OCR service is temporarily unavailable. Please try again later.'},
                504: {'error': 'timeout_error', 'message': 'Gateway timeout. Please try again.'}
            }
            
            error_info = veryfi_error_mapping.get(veryfi_status, {
                'error': 'veryfi_error',
                'message': error_message or 'OCR processing failed. Please try again.'
            })
            
            return create_response(
                error_info['message'],
                error=error_info['error'],
                status_code=500 if veryfi_status >= 500 else 400
            )
        
        import traceback
        traceback.print_exc()
        return create_response(
            'OCR processing failed',
            error='server_error',
            status_code=500
        )

