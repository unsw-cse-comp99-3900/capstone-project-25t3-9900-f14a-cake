"""Invoice service - handles invoice-related business logic."""
from models import db, Invoice
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import random
import string


def create_invoice_from_ocr(user_id: int, original_filename: str, ocr_data: dict, json_filename: str):
    """
    Create invoice record from OCR results.
    
    Args:
        user_id: User ID
        original_filename: Original uploaded filename
        ocr_data: OCR extracted JSON data
        json_filename: Saved JSON filename
    
    Returns:
        Invoice object
    """
    invoice = Invoice(
        user_id=user_id,
        filename=json_filename,
        original_filename=original_filename,
        ocr_data=ocr_data,
        status='ocr_completed'
    )
    
    db.session.add(invoice)
    db.session.commit()
    
    return invoice


def create_manual_invoice(user_id: int, invoice_data: dict):
    """
    Create manually entered invoice record.
    
    Args:
        user_id: User ID
        invoice_data: Invoice data JSON
    
    Returns:
        Invoice object
    """
    # Generate 6 random letters for filename
    random_letters = ''.join(random.choices(string.ascii_lowercase, k=6))
    json_filename = f"manual-data-{random_letters}.json"
    original_filename = f"manual-data-{random_letters}"
    
    invoice = Invoice(
        user_id=user_id,
        filename=json_filename,
        original_filename=original_filename,
        ocr_data=invoice_data,
        status='processed'  # Start with processed status for manual entry
    )
    
    db.session.add(invoice)
    db.session.commit()
    
    return invoice


def update_invoice_xml(invoice_id: int, xml_content: str):
    """
    Update invoice XML content.
    
    Args:
        invoice_id: Invoice ID
        xml_content: XML content string
    
    Returns:
        Invoice object or None if not found
    """
    invoice = db.session.get(Invoice, invoice_id)
    if not invoice:
        return None
    
    invoice.xml_content = xml_content
    invoice.status = 'xml_generated'
    invoice.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return invoice


def update_invoice_validation(invoice_id: int, validation_result: dict):
    """
    Update invoice validation result.
    
    Args:
        invoice_id: Invoice ID
        validation_result: Validation result JSON
    
    Returns:
        Invoice object or None if not found
    """
    invoice = db.session.get(Invoice, invoice_id)
    if not invoice:
        return None
    
    invoice.validation_result = validation_result
    invoice.status = 'validated' if validation_result.get('success', False) else 'validation_failed'
    invoice.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return invoice


def update_invoice_ocr_data(invoice_id: int, user_id: int, ocr_data: dict, preserve_status: bool = False):
    """
    Update invoice OCR data.
    
    Args:
        invoice_id: Invoice ID
        user_id: User ID (for permission verification)
        ocr_data: Updated OCR data JSON
        preserve_status: If True, preserve existing status and XML/validation results
                        (used when data hasn't changed)
    
    Returns:
        Invoice object or None if not found or access denied
    """
    invoice = db.session.get(Invoice, invoice_id)
    if not invoice:
        return None
    
    # Verify invoice belongs to the user
    if invoice.user_id != user_id:
        return None
    
    invoice.ocr_data = ocr_data
    invoice.updated_at = datetime.utcnow()
    
    if preserve_status:
        # If preserving status, don't change status, XML, or validation results
        pass
    else:
        # Reset status to processed, allowing XML regeneration
        invoice.status = 'processed'
        # Clear previous XML and validation results since OCR data was updated
        invoice.xml_content = None
        invoice.validation_result = None
    
    db.session.commit()
    
    return invoice


def get_user_invoices(user_id: int, page: int = 1, per_page: int = 20, status: str = None) -> dict:
    """
    Get user's invoice list with pagination.
    
    Args:
        user_id: User ID
        page: Page number (1-indexed)
        per_page: Number of items per page
        status: Optional status filter
    
    Returns:
        Dictionary with 'items' (list of invoices) and 'pagination' (pagination info)
    """
    query = Invoice.query.filter_by(user_id=user_id)
    
    if status:
        query = query.filter_by(status=status)
    
    query = query.order_by(Invoice.created_at.desc())
    
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return {
        'items': [invoice.to_dict() for invoice in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_num': pagination.prev_num,
            'next_num': pagination.next_num
        }
    }


def get_invoice_by_id(invoice_id: int, user_id: int = None):
    """
    Get invoice by ID with optional user ID verification.
    
    Args:
        invoice_id: Invoice ID
        user_id: Optional user ID (if provided, verifies invoice belongs to user)
    
    Returns:
        Invoice object or None if not found or access denied
    """
    invoice = db.session.get(Invoice, invoice_id)
    
    if not invoice:
        return None
    
    # If user_id provided, verify invoice belongs to the user
    if user_id and invoice.user_id != user_id:
        return None
    
    return invoice


def get_all_invoices(page: int = 1, per_page: int = 20, status: str = None, user_id: int = None) -> dict:
    """
    Get all invoices list (admin function) with filtering support.
    
    Args:
        page: Page number (1-indexed)
        per_page: Number of items per page
        status: Optional status filter
        user_id: Optional user ID filter
    
    Returns:
        Dictionary with 'items' (list of invoices) and 'pagination' (pagination info)
    """
    query = Invoice.query
    
    if status:
        query = query.filter_by(status=status)
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    query = query.order_by(Invoice.created_at.desc())
    
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return {
        'items': [invoice.to_dict() for invoice in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_num': pagination.prev_num,
            'next_num': pagination.next_num
        }
    }


def delete_invoice(invoice_id: int, user_id: int) -> bool:
    """
    Delete an invoice (user can only delete their own invoices).
    
    Args:
        invoice_id: Invoice ID
        user_id: User ID (for permission verification)
    
    Returns:
        True if deleted successfully, False otherwise
    """
    invoice = db.session.get(Invoice, invoice_id)
    
    if not invoice:
        return False
    
    # Verify invoice belongs to the user
    if invoice.user_id != user_id:
        return False
    
    # Delete associated files if they exist
    try:
        if invoice.filename and os.path.exists(invoice.filename):
            os.remove(invoice.filename)
    except Exception as e:
        # Log error but continue with deletion
        print(f'Error deleting file {invoice.filename}: {str(e)}')
    
    db.session.delete(invoice)
    db.session.commit()
    
    return True

