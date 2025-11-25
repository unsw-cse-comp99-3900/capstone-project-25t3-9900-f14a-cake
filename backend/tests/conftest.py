"""Pytest configuration and shared fixtures."""
import os
import pytest
import tempfile
from flask import Flask
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret-key-for-testing'
os.environ['FLASK_ENV'] = 'testing'


# Import application components
from models import db, User, Invoice, EmailVerificationCode, bcrypt
from utils.auth import AuthManager, create_tokens
from routes.auth_routes import auth_bp
from routes.invoices_routes import invoices_bp
from routes.admin_routes import admin_bp
from routes.ocr_routes import ocr_bp
from routes.xml_routes import xml_bp
from routes.email_routes import email_bp
from datetime import datetime, timedelta
import time 


@pytest.fixture(scope='session')
def app():
    """Create test Flask application instance."""
    # Create new Flask application instance for testing
    test_app = Flask(__name__)
    CORS(test_app)
    
    # Use SQLite temporary file database for testing
    test_db_fd, test_db_path = tempfile.mkstemp(suffix='.db')
    os.close(test_db_fd)
    
    test_app.config['TESTING'] = True
    test_app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{test_db_path}'
    test_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    test_app.config['JWT_SECRET_KEY'] = 'test-jwt-secret-key-for-testing'
    test_app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600
    test_app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 2592000
    test_app.config['JWT_BLACKLIST_ENABLED'] = False
    test_app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    test_app.config['JWT_CSRF_CHECK_FORM'] = False
    
    # Create temporary upload folder
    test_app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    test_app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    
    # Initialize extensions
    db.init_app(test_app)
    bcrypt.init_app(test_app)
    
    # Initialize JWT
    auth_manager = AuthManager()
    auth_manager.init_app(test_app)
    
    # Register blueprints
    test_app.register_blueprint(auth_bp, url_prefix='/api')
    test_app.register_blueprint(invoices_bp, url_prefix='/api')
    test_app.register_blueprint(admin_bp, url_prefix='/api')
    test_app.register_blueprint(ocr_bp, url_prefix='/api')
    test_app.register_blueprint(xml_bp, url_prefix='/api')
    test_app.register_blueprint(email_bp, url_prefix='/api')
    
    # Create all tables
    with test_app.app_context():
        db.create_all()
    
    yield test_app
    
    # Cleanup - ensure all connections are closed
    with test_app.app_context():
        # Clean up database session
        db.session.remove()
        # Drop all tables
        db.drop_all()
        # Close and clean up database engine connections
        db.engine.dispose()
    
    # Clean up temporary files - with retry logic
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            if os.path.exists(test_db_path):
                os.unlink(test_db_path)
            break
        except PermissionError:
            if attempt < max_attempts - 1:
                time.sleep(0.1)  # Wait before retry
            else:
                print(f"Warning: Unable to delete test database file {test_db_path}")


@pytest.fixture
def db_session(app):    
    with app.app_context():
        db.create_all()
        
        # Create a session manually for the test
        session = db.session
        
        try:
            yield session
        finally:
            # Handle the session cleanup properly
            try:
                session.rollback()
            except:
                pass
            
            # Check if remove method exists before calling it
            if hasattr(session, 'remove'):
                session.remove()
            else:
                # For SQLAlchemy 2.0+, just close the session
                session.close()
            
            db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def test_user(db_session):
    """Create test user."""
    user = User(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        role='user'
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    """Create admin user."""
    admin = User(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
        role='admin'
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin

@pytest.fixture
def user_factory(db_session):
    """User factory fixture."""
    def _create_user(**kwargs):
        user_data = {
            'username': f'testuser_{len(db_session.query(User).all())}',
            'email': f'test{len(db_session.query(User).all())}@example.com',
            'password': 'testpass123',
            'role': 'user',
            'is_active': True
        }
        user_data.update(kwargs)
        
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    return _create_user


@pytest.fixture
def invoice_factory(db_session):
    """Invoice factory fixture."""
    def _create_invoice(**kwargs):
        # If user_id not provided, need to provide a default user
        if 'user_id' not in kwargs:
            # Create a default user (if needed)
            default_user = db_session.query(User).first()
            if not default_user:
                default_user = User(
                    username='default_test_user',
                    email='default@example.com',
                    password='testpass123',
                    role='user',
                    is_active=True
                )
                db_session.add(default_user)
                db_session.commit()
            kwargs['user_id'] = default_user.id
            
        invoice_data = {
            'filename': f'test_invoice_{len(db_session.query(Invoice).all())}.json',
            'original_filename': f'original_{len(db_session.query(Invoice).all())}.pdf',
            'ocr_data': {'test': 'data'},
            'status': 'processed'
        }
        invoice_data.update(kwargs)
        
        invoice = Invoice(**invoice_data)
        db_session.add(invoice)
        db_session.commit()
        db_session.refresh(invoice)
        return invoice
    
    return _create_invoice

@pytest.fixture
def auth_headers(app, test_user):
    """Generate authentication headers."""
    with app.app_context():
        tokens = create_tokens(test_user)
        return {
            'Authorization': f"Bearer {tokens['access_token']}"
        }


@pytest.fixture
def admin_headers(app, admin_user):
    """Generate admin authentication headers."""
    with app.app_context():
        tokens = create_tokens(admin_user)
        return {
            'Authorization': f"Bearer {tokens['access_token']}"
        }


@pytest.fixture
def auth_client(client, auth_headers):
    """Test client with authentication."""
    def _make_request(method, url, **kwargs):
        headers = kwargs.pop('headers', {})
        headers.update(auth_headers)
        kwargs['headers'] = headers
        return getattr(client, method.lower())(url, **kwargs)
    
    return _make_request


@pytest.fixture
def create_verification_code(db_session):
    """Helper function to create verification code."""
    def _create_code(email, code=None, expires_in_minutes=2):
        """Create verification code.
        
        Args:
            email: Email address
            code: Verification code (auto-generated if None)
            expires_in_minutes: Expiration time in minutes
        
        Returns:
            EmailVerificationCode object
        """
        if code is None:
            import secrets
            import string
            code = ''.join(secrets.choice(string.digits) for _ in range(6))
        
        verification_code = EmailVerificationCode(email=email)
        verification_code.code = code
        verification_code.expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        verification_code.is_used = False
        verification_code.is_invalidated = False
        
        db_session.add(verification_code)
        db_session.commit()
        
        return verification_code
    
    return _create_code


@pytest.fixture
def sample_invoice_data():
    """Sample invoice data."""
    return {
        'invoice_number': 'INV-001',
        'issue_date': '2024-01-15',
        'due_date': '2024-02-15',
        'currency_code': 'AUD',
        'supplier': {
            'name': 'Test Supplier',
            'abn': '12345678901'
        },
        'customer': {
            'name': 'Test Customer',
            'abn': '98765432109'
        },
        'line_items': [
            {
                'name': 'Test Item',
                'quantity': 1.0,
                'unit_price': 100.0,
                'line_total': 100.0
            }
        ],
        'summary': {
            'subtotal': 100.0,
            'tax_amount': 10.0,
            'total': 110.0
        }
    }


@pytest.fixture
def sample_ocr_data():
    """Sample OCR data."""
    return {
        'document_type': 'invoice',
        'invoice_number': 'INV-001',
        'date': '2024-01-15',
        'due_date': '2024-02-15',
        'currency_code': 'AUD',
        'vendor': {
            'name': 'Test Vendor',
            'raw_name': 'Test Vendor Pty Ltd'
        },
        'bill_to': {
            'name': 'Test Customer',
            'address': '123 Test St'
        },
        'line_items': [
            {
                'description': 'Test Item',
                'quantity': 1.0,
                'price': 100.0,
                'total': 100.0
            }
        ],
        'subtotal': 100.0,
        'tax': 10.0,
        'total': 110.0
    }


