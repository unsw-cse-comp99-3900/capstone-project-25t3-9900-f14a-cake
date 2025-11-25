"""Model unit tests."""
import pytest
from models import User, Invoice, db, bcrypt
from datetime import datetime


@pytest.mark.unit
class TestUserModel:
    """User model tests."""
    
    def test_user_creation(self, db_session):
        """Test user creation."""
        user = User(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.role == 'user'
        assert user.is_active is True
        assert user.password_hash is not None
        assert user.password_hash != 'testpass123'  # Password should be hashed
    
    def test_user_password_hashing(self, db_session):
        """Test password hashing."""
        user = User(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Password should be hashed
        assert user.password_hash != 'testpass123'
        assert len(user.password_hash) > 0
    
    def test_user_password_verification(self, db_session):
        """Test password verification."""
        user = User(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Correct password should verify
        assert user.check_password('testpass123') is True
        
        # Wrong password should fail verification
        assert user.check_password('wrongpassword') is False
    
    def test_user_to_dict(self, db_session):
        """Test user serialization."""
        user = User(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        db_session.add(user)
        db_session.commit()
        
        user_dict = user.to_dict()
        
        assert 'id' in user_dict
        assert 'username' in user_dict
        assert 'email' in user_dict
        assert 'role' in user_dict
        assert 'is_active' in user_dict
        assert 'created_at' in user_dict
        assert 'updated_at' in user_dict
        assert 'password_hash' not in user_dict  # Password hash should not be in dict
    
    def test_user_unique_constraints(self, db_session):
        """Test user uniqueness constraints."""
        user1 = User(
            username='testuser',
            email='test1@example.com',
            password='testpass123'
        )
        db_session.add(user1)
        db_session.commit()
        
        # Attempting to create user with same username should fail
        user2 = User(
            username='testuser',
            email='test2@example.com',
            password='testpass123'
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
    
    def test_user_email_unique_constraints(self, db_session):
        """Test email uniqueness constraints."""
        user1 = User(
            username='user1',
            email='test@example.com',
            password='testpass123'
        )
        db_session.add(user1)
        db_session.commit()
        
        # Attempting to create user with same email should fail
        user2 = User(
            username='user2',
            email='test@example.com',
            password='testpass123'
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
    
    def test_user_role_default(self, db_session):
        """Test user role default value."""
        user = User(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        assert user.role == 'user'
    
    def test_user_invoices_relationship(self, db_session, test_user):
        """Test user and invoice relationship."""
        invoice = Invoice(
            user_id=test_user.id,
            filename='test.json',
            original_filename='test.pdf',
            ocr_data={'test': 'data'}
        )
        db_session.add(invoice)
        db_session.commit()
        
        # Test relationship
        assert len(test_user.invoices) == 1
        assert test_user.invoices[0].id == invoice.id
        assert invoice.user.id == test_user.id


@pytest.mark.unit
class TestInvoiceModel:
    """Invoice model tests."""
    
    def test_invoice_creation(self, db_session, test_user):
        """Test invoice creation."""
        invoice = Invoice(
            user_id=test_user.id,
            filename='test_invoice.json',
            original_filename='MyInvoice.pdf',
            ocr_data={'vendor': 'Test Vendor', 'amount': 100.50},
            status='ocr_completed'
        )
        db_session.add(invoice)
        db_session.commit()
        
        assert invoice.id is not None
        assert invoice.user_id == test_user.id
        assert invoice.filename == 'test_invoice.json'
        assert invoice.original_filename == 'MyInvoice.pdf'
        assert invoice.status == 'ocr_completed'
        assert invoice.ocr_data == {'vendor': 'Test Vendor', 'amount': 100.50}
    
    def test_invoice_default_status(self, db_session, test_user):
        """Test invoice default status."""
        # Create invoice without explicitly setting status
        invoice = Invoice(
            user_id=test_user.id,
            filename='test.json',
            original_filename='test.pdf'
        )
        
        # The status should be None before adding to the database
        print(f"Status before adding to session: {repr(invoice.status)}")
        
        # Add to session
        db_session.add(invoice)
        
        # The status should still be None before flush/commit
        print(f"Status after adding to session: {repr(invoice.status)}")
        
        # Flush triggers the default value from the database
        db_session.flush()
        print(f"Status after flush: {repr(invoice.status)}")
        
        # Commit the transaction
        db_session.commit()
        print(f"Status after commit: {repr(invoice.status)}")
        
        # Refresh to ensure we have the latest from the database
        db_session.refresh(invoice)
        print(f"Status after refresh: {repr(invoice.status)}")
        
        assert invoice.status == 'processed'
    
    def test_invoice_to_dict(self, db_session, test_user):
        """Test invoice serialization."""
        invoice = Invoice(
            user_id=test_user.id,
            filename='test.json',
            original_filename='test.pdf',
            ocr_data={'test': 'data'},
            xml_content='<xml>test</xml>',
            validation_result={'valid': True}
        )
        db_session.add(invoice)
        db_session.commit()
        
        invoice_dict = invoice.to_dict()
        
        assert 'id' in invoice_dict
        assert 'user_id' in invoice_dict
        assert 'filename' in invoice_dict
        assert 'original_filename' in invoice_dict
        assert 'ocr_data' in invoice_dict
        assert 'xml_content' in invoice_dict
        assert 'validation_result' in invoice_dict
        assert 'status' in invoice_dict
        assert 'created_at' in invoice_dict
        assert 'updated_at' in invoice_dict
    
    def test_invoice_cascade_delete(self, db_session, test_user):
        """Test cascade delete."""
        invoice = Invoice(
            user_id=test_user.id,
            filename='test.json',
            original_filename='test.pdf'
        )
        db_session.add(invoice)
        db_session.commit()
        
        invoice_id = invoice.id
        
        # Delete user, invoice should be cascade deleted
        db_session.delete(test_user)
        db_session.commit()
        
        # Verify invoice was also deleted
        deleted_invoice = db_session.get(Invoice, invoice_id)
        assert deleted_invoice is None

