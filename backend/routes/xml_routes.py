"""XML generation and validation routes."""
from flask import Blueprint, request, jsonify, current_app, send_file, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.xml_generator import generate_ubl_xml
from services.xml_validator import validate_xml
from services.token_manager import get_token_manager
from services.invoice_service import update_invoice_xml, update_invoice_validation, get_invoice_by_id
from utils.helpers import create_response
from datetime import datetime
from werkzeug.utils import secure_filename
from typing import Tuple, Optional
import os
import config

xml_bp = Blueprint('xml', __name__)


@xml_bp.route('/upload-xml', methods=['POST'])
@jwt_required()
def handle_upload_xml() -> Tuple[Response, int]:
    """
    Upload XML file for validation.
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    try:
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
        if not file.filename.lower().endswith('.xml'):
            return create_response(
                'Invalid file type. Only XML files are supported for validation.',
                error='validation_error',
                status_code=400
            )
        
        # Read XML content
        xml_content = file.read().decode('utf-8')
        
        # Save file (with timestamp)
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = os.path.splitext(filename)[0]
        saved_filename = f"{base_name}_{timestamp}.xml"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], saved_filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        current_app.logger.info(f"XML file uploaded: {saved_filename}")
        
        return create_response(
            'XML file uploaded successfully',
            data={
            'xml_content': xml_content,
            'filename': saved_filename,
                'file_created_at': int(datetime.now().timestamp())
            },
            status_code=200
        )
        
    except UnicodeDecodeError:
        return create_response(
            'Invalid XML file. The file cannot be decoded as UTF-8. Please ensure it is a valid XML file.',
            error='validation_error',
            status_code=400
        )
    except Exception as e:
        current_app.logger.error(f"Error uploading XML: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(
            'XML upload failed',
            error='server_error',
            status_code=500
        )


@xml_bp.route('/generate-xml', methods=['POST'])
@jwt_required()
def handle_generate_xml() -> Tuple[Response, int]:
    """
    Generate UBL XML format invoice from form data.
    
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
        
        # Get current user ID
        user_id = int(get_jwt_identity())
        
        # Get invoice ID (if provided)
        invoice_id = data.get('invoice_id')
        
        # Generate XML
        xml_content = generate_ubl_xml(data)
        
        # Save XML file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        xml_filename = f"invoice_{timestamp}.xml"
        xml_path = os.path.join(current_app.config['UPLOAD_FOLDER'], xml_filename)
        
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        # If invoice_id provided, update invoice record
        if invoice_id:
            invoice = get_invoice_by_id(invoice_id, user_id)
            if invoice:
                update_invoice_xml(invoice_id, xml_content)
                current_app.logger.info(f"Updated invoice {invoice_id} with XML content")
        
        current_app.logger.info(f"XML generated: {xml_path}")
        
        return create_response(
            'XML generated successfully',
            data={
            'xml_content': xml_content,
            'filename': xml_filename,
                'invoice_id': invoice_id
            },
            status_code=200
        )
        
    except Exception as e:
        current_app.logger.error(f"Error generating XML: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(
            'XML generation failed',
            error='server_error',
            status_code=500
        )


@xml_bp.route('/validate-xml', methods=['POST'])
@jwt_required()
def handle_validate_xml() -> Response:
    """
    Validate XML invoice (both rules must pass, supports automatic token refresh).
    
    Returns:
        Flask JSON response
    """
    try:
        data = request.get_json()
        
        if not data or 'xml_content' not in data:
            return create_response(
                'No XML content provided',
                error='validation_error',
                status_code=400
            )
        
        xml_content = data['xml_content']
        invoice_id = data.get('invoice_id')
        user_id = int(get_jwt_identity())
        
        # Get token manager
        token_manager = get_token_manager()
        
        # Get current valid token
        try:
            current_token = token_manager.get_token()
        except Exception as e:
            current_app.logger.error(f"Failed to get token: {str(e)}")
            # If auto-fetch fails, try using token from environment variables
            current_token = config.ESS_VALIDATOR_TOKEN
            if not current_token:
                return create_response(
                    'ESS Validator token not available',
                    error='configuration_error',
                    status_code=500
                )
        
        # Call validation service (pass token_manager to support auto-refresh)
        result = validate_xml(xml_content, current_token, token_manager)
        
        # If invoice_id provided, update invoice validation result
        if invoice_id:
            invoice = get_invoice_by_id(invoice_id, user_id)
            if invoice:
                update_invoice_validation(invoice_id, result)
                current_app.logger.info(f"Updated invoice {invoice_id} with validation result")
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error validating XML: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(
            'XML validation failed',
            error='server_error',
            status_code=500
        )


@xml_bp.route('/download-json/<filename>', methods=['GET'])
@jwt_required()
def handle_download_json(filename: str) -> Response:
    """
    Download OCR-generated JSON file.
    
    Args:
        filename: Name of the JSON file to download
    
    Returns:
        Flask file response or error response
    """
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return create_response(
                'File not found. The file has been deleted (files are auto-deleted after 30 minutes). Please re-upload and process the document.',
                error='file_not_found',
                status_code=404
            )
        
        return send_file(
            file_path,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        current_app.logger.error(f"Error downloading file: {str(e)}")
        return create_response(
            'File download failed',
            error='server_error',
            status_code=500
        )
