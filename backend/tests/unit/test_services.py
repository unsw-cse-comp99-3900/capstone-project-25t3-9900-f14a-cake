"""Service layer unit tests."""
import pytest
from models import Invoice, db
from services.invoice_service import (
    create_invoice_from_ocr,
    update_invoice_xml,
    update_invoice_validation,
    get_user_invoices,
    get_invoice_by_id,
    get_all_invoices
)


@pytest.mark.unit
class TestInvoiceService:
    """Invoice service tests."""
    
    def test_create_invoice_from_ocr(self, db_session, test_user):
        """Test create invoice from OCR."""
        ocr_data = {
            'invoice_number': 'INV-001',
            'total': 100.50,
            'vendor': {'name': 'Test Vendor'}
        }
        
        invoice = create_invoice_from_ocr(
            user_id=test_user.id,
            original_filename='test.pdf',
            ocr_data=ocr_data,
            json_filename='test_result.json'
        )
        
        assert invoice.id is not None
        assert invoice.user_id == test_user.id
        assert invoice.original_filename == 'test.pdf'
        assert invoice.filename == 'test_result.json'
        assert invoice.ocr_data == ocr_data
        assert invoice.status == 'ocr_completed'
    
    def test_update_invoice_xml(self, db_session, test_user):
        """Test update invoice XML."""
        invoice = Invoice(
            user_id=test_user.id,
            filename='test.json',
            original_filename='test.pdf',
            status='ocr_completed'
        )
        db_session.add(invoice)
        db_session.commit()
        
        xml_content = '<?xml version="1.0"?><invoice>test</invoice>'
        updated = update_invoice_xml(invoice.id, xml_content)
        
        assert updated is not None
        assert updated.xml_content == xml_content
        assert updated.status == 'xml_generated'
    
    def test_update_invoice_xml_not_found(self, db_session):
        """Test update non-existent invoice."""
        result = update_invoice_xml(99999, '<xml>test</xml>')
        assert result is None
    
    def test_update_invoice_validation(self, db_session, test_user):
        """Test update invoice validation result."""
        invoice = Invoice(
            user_id=test_user.id,
            filename='test.json',
            original_filename='test.pdf',
            status='xml_generated'
        )
        db_session.add(invoice)
        db_session.commit()
        
        validation_result = {'success': True, 'valid': True}
        updated = update_invoice_validation(invoice.id, validation_result)
        
        assert updated is not None
        assert updated.validation_result == validation_result
        assert updated.status == 'validated'
    
    def test_update_invoice_validation_failed(self, db_session, test_user):
        """Test validation failure case."""
        invoice = Invoice(
            user_id=test_user.id,
            filename='test.json',
            original_filename='test.pdf',
            status='xml_generated'
        )
        db_session.add(invoice)
        db_session.commit()
        
        validation_result = {'success': False, 'errors': ['Invalid format']}
        updated = update_invoice_validation(invoice.id, validation_result)
        
        assert updated.status == 'validation_failed'
    
    def test_get_user_invoices(self, db_session, test_user, invoice_factory):
        """Test get user invoice list."""
        # Create multiple invoices
        invoice1 = invoice_factory(user_id=test_user.id)
        invoice2 = invoice_factory(user_id=test_user.id)
        
        result = get_user_invoices(test_user.id, page=1, per_page=10)
        
        assert 'items' in result
        assert 'pagination' in result
        assert len(result['items']) == 2
        assert result['pagination']['total'] == 2
    
    def test_get_user_invoices_pagination(self, db_session, test_user, invoice_factory):
        """Test invoice list pagination."""
        # Create 15 invoices
        for _ in range(15):
            invoice_factory(user_id=test_user.id)
        
        # First page
        result1 = get_user_invoices(test_user.id, page=1, per_page=10)
        assert len(result1['items']) == 10
        assert result1['pagination']['has_next'] is True
        
        # Second page
        result2 = get_user_invoices(test_user.id, page=2, per_page=10)
        assert len(result2['items']) == 5
        assert result2['pagination']['has_next'] is False
    
    def test_get_user_invoices_status_filter(self, db_session, test_user, invoice_factory):
        """Test invoice status filter."""
        invoice_factory(user_id=test_user.id, status='ocr_completed')
        invoice_factory(user_id=test_user.id, status='xml_generated')
        invoice_factory(user_id=test_user.id, status='validated')
        
        result = get_user_invoices(test_user.id, page=1, per_page=10, status='ocr_completed')
        
        assert len(result['items']) == 1
        assert result['items'][0]['status'] == 'ocr_completed'
    
    def test_get_invoice_by_id(self, db_session, test_user):
        """Test get invoice by ID."""
        invoice = Invoice(
            user_id=test_user.id,
            filename='test.json',
            original_filename='test.pdf'
        )
        db_session.add(invoice)
        db_session.commit()
        
        found = get_invoice_by_id(invoice.id)
        assert found is not None
        assert found.id == invoice.id
    
    def test_get_invoice_by_id_with_user_verification(self, db_session, test_user, user_factory):
        """Test get invoice with user verification."""
        other_user = user_factory()
        
        invoice = Invoice(
            user_id=test_user.id,
            filename='test.json',
            original_filename='test.pdf'
        )
        db_session.add(invoice)
        db_session.commit()
        
        # Correct user should be able to get
        found = get_invoice_by_id(invoice.id, test_user.id)
        assert found is not None
        
        # Other user should not be able to get
        found = get_invoice_by_id(invoice.id, other_user.id)
        assert found is None
    
    def test_get_all_invoices(self, db_session, test_user, user_factory, invoice_factory):
        """Test get all invoices (admin function)."""
        other_user = user_factory()
        
        # Create invoices for two users
        invoice_factory(user_id=test_user.id)
        invoice_factory(user_id=other_user.id)
        
        result = get_all_invoices(page=1, per_page=10)
        
        assert len(result['items']) == 2
    
    def test_get_all_invoices_user_filter(self, db_session, test_user, user_factory, invoice_factory):
        """Test filter all invoices by user."""
        other_user = user_factory()
        
        invoice_factory(user_id=test_user.id)
        invoice_factory(user_id=other_user.id)
        
        result = get_all_invoices(page=1, per_page=10, user_id=test_user.id)
        
        assert len(result['items']) == 1
        assert result['items'][0]['user_id'] == test_user.id

