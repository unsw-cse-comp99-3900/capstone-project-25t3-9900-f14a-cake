"""Invoice record related routes."""
from flask import Blueprint, request, jsonify, current_app, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Invoice
from services.invoice_service import (
    get_user_invoices, get_invoice_by_id, get_all_invoices, update_invoice_ocr_data, delete_invoice,
    create_manual_invoice
)
from utils.auth import admin_required
from utils.helpers import create_response
from typing import Tuple

invoices_bp = Blueprint('invoices', __name__)


@invoices_bp.route('/invoices/manual', methods=['POST'])
@jwt_required()
def create_manual_invoice_record() -> Tuple[Response, int]:
    """
    Create manually entered invoice record.
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        if not data or 'invoice_data' not in data:
            return create_response(
                'Invoice data is required',
                error='validation_error',
                status_code=400
            )
        
        invoice = create_manual_invoice(
            user_id=user_id,
            invoice_data=data['invoice_data']
        )
        
        return create_response(
            'Manual invoice created successfully',
            data={'invoice': invoice.to_dict()},
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Create manual invoice error: {str(e)}')
        return create_response(
            'Failed to create manual invoice',
            error='server_error',
            status_code=500
        )


@invoices_bp.route('/invoices', methods=['GET'])
@jwt_required()
def get_my_invoices() -> Tuple[Response, int]:
    """
    Get current user's invoice list.
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    try:
        user_id = int(get_jwt_identity())
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', None, type=str)
        
        # Limit maximum items per page
        per_page = min(per_page, 100)
        
        result = get_user_invoices(
            user_id=user_id,
            page=page,
            per_page=per_page,
            status=status
        )
        
        return create_response(
            'Invoices retrieved successfully',
            data=result,
            status_code=200
        )
        
    except Exception as e:
        current_app.logger.error(f'Get invoices error: {str(e)}')
        return create_response(
            'Failed to retrieve invoices',
            error='server_error',
            status_code=500
        )


@invoices_bp.route('/invoices/<int:invoice_id>', methods=['GET'])
@jwt_required()
def get_invoice_detail(invoice_id: int) -> Tuple[Response, int]:
    """
    Get specific invoice details.
    
    Args:
        invoice_id: Invoice ID
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    try:
        user_id = int(get_jwt_identity())
        
        invoice = get_invoice_by_id(invoice_id, user_id)
        
        if not invoice:
            return create_response(
                'Invoice not found',
                error='invoice_not_found',
                status_code=404
            )
        
        return create_response(
            'Invoice retrieved successfully',
            data={'invoice': invoice.to_dict()},
            status_code=200
        )
        
    except Exception as e:
        current_app.logger.error(f'Get invoice detail error: {str(e)}')
        return create_response(
            'Failed to retrieve invoice',
            error='server_error',
            status_code=500
        )


@invoices_bp.route('/invoices/<int:invoice_id>', methods=['PUT'])
@jwt_required()
def update_invoice(invoice_id: int) -> Tuple[Response, int]:
    """
    Update invoice OCR data.
    
    Args:
        invoice_id: Invoice ID
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        if not data or 'ocr_data' not in data:
            return create_response(
                'OCR data is required',
                error='validation_error',
                status_code=400
            )
        
        # Check if preserve_status flag is provided
        preserve_status = data.get('preserve_status', False)
        
        invoice = update_invoice_ocr_data(
            invoice_id=invoice_id,
            user_id=user_id,
            ocr_data=data['ocr_data'],
            preserve_status=preserve_status
        )
        
        if not invoice:
            return create_response(
                'Invoice not found or access denied',
                error='invoice_not_found',
                status_code=404
            )
        
        return create_response(
            'Invoice updated successfully',
            data={'invoice': invoice.to_dict()},
            status_code=200
        )
        
    except Exception as e:
        current_app.logger.error(f'Update invoice error: {str(e)}')
        return create_response(
            'Failed to update invoice',
            error='server_error',
            status_code=500
        )


@invoices_bp.route('/invoices/<int:invoice_id>', methods=['DELETE'])
@jwt_required()
def delete_invoice_record(invoice_id: int) -> Tuple[Response, int]:
    """
    Delete an invoice record.
    
    Args:
        invoice_id: Invoice ID
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    try:
        user_id = int(get_jwt_identity())
        
        success = delete_invoice(invoice_id, user_id)
        
        if not success:
            return create_response(
                'Invoice not found or access denied',
                error='invoice_not_found',
                status_code=404
            )
        
        return create_response(
            'Invoice deleted successfully',
            status_code=200
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Delete invoice error: {str(e)}')
        return create_response(
            'Failed to delete invoice',
            error='server_error',
            status_code=500
        )


@invoices_bp.route('/admin/invoices', methods=['GET'])
@jwt_required()
@admin_required
def get_all_invoices_admin() -> Tuple[Response, int]:
    """
    Admin: Get all invoices list.
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', None, type=str)
        user_id = request.args.get('user_id', None, type=int)
        
        # Limit maximum items per page
        per_page = min(per_page, 100)
        
        result = get_all_invoices(
            page=page,
            per_page=per_page,
            status=status,
            user_id=user_id
        )
        
        return create_response(
            'All invoices retrieved successfully',
            data=result,
            status_code=200
        )
        
    except Exception as e:
        current_app.logger.error(f'Get all invoices error: {str(e)}')
        return create_response(
            'Failed to retrieve invoices',
            error='server_error',
            status_code=500
        )

