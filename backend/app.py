"""Main Flask application"""
from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
import os
import config
from routes.ocr_routes import ocr_bp
from routes.xml_routes import xml_bp
from routes.email_routes import email_bp
from services.file_cleanup import start_cleanup_service, stop_cleanup_service
from services.token_manager import get_token_manager
from models import db, bcrypt
from utils.auth import AuthManager
import atexit

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://invoice_user:invoice_db_password@db:5432/invoice_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and migrations
db.init_app(app)
bcrypt.init_app(app)
migrate = Migrate(app, db)

# Initialize JWT authentication
auth_manager = AuthManager()
auth_manager.init_app(app)

# Create upload folder
if not os.path.exists(config.UPLOAD_FOLDER):
    os.makedirs(config.UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_FILE_SIZE_MB * 1024 * 1024

# Register blueprints
app.register_blueprint(ocr_bp, url_prefix='/api')
app.register_blueprint(xml_bp, url_prefix='/api')
app.register_blueprint(email_bp, url_prefix='/api')

# Register authentication blueprint
from routes.auth_routes import auth_bp
app.register_blueprint(auth_bp, url_prefix='/api')

# Register invoice routes blueprint
from routes.invoices_routes import invoices_bp
app.register_blueprint(invoices_bp, url_prefix='/api')

# Register admin routes blueprint
from routes.admin_routes import admin_bp
app.register_blueprint(admin_bp, url_prefix='/api')

# Initialize token manager
token_manager = get_token_manager()

# Start file cleanup service
cleanup_service = start_cleanup_service(
    upload_folder=config.UPLOAD_FOLDER,
    max_age_minutes=config.FILE_MAX_AGE_MINUTES,
    check_interval_minutes=config.FILE_CLEANUP_INTERVAL_MINUTES
)

# Stop cleanup service when application closes
atexit.register(stop_cleanup_service)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'message': 'API is running'})


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    return jsonify({
        'error': 'File too large',
        'message': f'File size exceeds the {config.MAX_FILE_SIZE_MB}MB limit. Please upload a smaller file.',
        'max_size_mb': config.MAX_FILE_SIZE_MB
    }), 413


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("E-Invoice API Server Starting...")
    print("=" * 60)
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"JWT Secret: {'Configured' if os.getenv('JWT_SECRET_KEY') else 'NOT CONFIGURED'}")
    print(f"Allowed file types: {', '.join(sorted(config.ALLOWED_EXTENSIONS))}")
    print(f"Max file size: {config.MAX_FILE_SIZE_MB}MB")
    print(f"Veryfi CLIENT_ID: {'Configured' if config.VERYFI_CLIENT_ID else 'NOT CONFIGURED'}")
    print(f"Veryfi AUTHORIZATION: {'Configured' if config.VERYFI_AUTHORIZATION else 'NOT CONFIGURED'}")
    print(f"ESS Validator token: {'Configured' if config.ESS_VALIDATOR_TOKEN else 'NOT CONFIGURED'}")
    
    # Display configuration warnings
    for warning in config.check_config():
        print(warning)
    
    print("=" * 60 + "\n")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        stop_cleanup_service()
