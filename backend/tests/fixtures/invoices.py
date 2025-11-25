"""Invoice test data fixtures."""
import pytest
from faker import Faker
from models import Invoice, db

fake = Faker()


@pytest.fixture
def invoice_factory(db_session):
    """Invoice factory function - requires user_id to be provided when used."""
    def _create_invoice(**kwargs):
        defaults = {
            'filename': f'invoice_{fake.uuid4()}.json',
            'original_filename': f'{fake.word()}_invoice.pdf',
            'ocr_data': {
                'invoice_number': fake.bothify('INV-####'),
                'total': float(fake.pydecimal(left_digits=3, right_digits=2, positive=True)),
                'date': fake.date().isoformat()
            },
            'status': 'ocr_completed'
        }
        defaults.update(kwargs)
        
        # user_id must be provided in kwargs
        if 'user_id' not in defaults:
            raise ValueError("user_id must be provided when creating an invoice")
        
        invoice = Invoice(**defaults)
        db_session.add(invoice)
        db_session.commit()
        db_session.refresh(invoice)
        return invoice
    
    return _create_invoice


@pytest.fixture
def multiple_invoices(invoice_factory, test_user):
    """Create multiple test invoices."""
    invoices = []
    for i in range(10):
        invoice = invoice_factory(
            user_id=test_user.id,
            original_filename=f'invoice_{i}.pdf',
            status=['ocr_completed', 'xml_generated', 'validated'][i % 3]
        )
        invoices.append(invoice)
    return invoices
