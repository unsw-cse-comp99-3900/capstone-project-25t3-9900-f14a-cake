"""Main Flask application"""
from flask import Flask, jsonify
from flask_cors import CORS
import os
import config
from routes.ocr_routes import ocr_bp
from routes.xml_routes import xml_bp
from routes.email_routes import email_bp
from services.file_cleanup import start_cleanup_service, stop_cleanup_service
from services.token_manager import get_token_manager
import atexit

app = Flask(__name__)
CORS(app)

# create upload file
if not os.path.exists(config.UPLOAD_FOLDER):
    os.makedirs(config.UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_FILE_SIZE_MB * 1024 * 1024

# register buleprint
app.register_blueprint(ocr_bp, url_prefix='/api')
app.register_blueprint(xml_bp, url_prefix='/api')
app.register_blueprint(email_bp, url_prefix='/api')

# init token manager
token_manager = get_token_manager()

# start cleanup service
cleanup_service = start_cleanup_service(
    upload_folder=config.UPLOAD_FOLDER,
    max_age_minutes=config.FILE_MAX_AGE_MINUTES,
    check_interval_minutes=config.FILE_CLEANUP_INTERVAL_MINUTES
)

# stop cleanup service
atexit.register(stop_cleanup_service)


@app.route('/api/health', methods=['GET'])
def health_check():
    """check health"""
    return jsonify({'status': 'ok', 'message': 'API is running'})


@app.errorhandler(413)
def request_entity_too_large(error):
    """handle file too large"""
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
    print(f"Allowed file types: {', '.join(sorted(config.ALLOWED_EXTENSIONS))}")
    print(f"Max file size: {config.MAX_FILE_SIZE_MB}MB")
    print(f"Veryfi CLIENT_ID: {'Configured' if config.VERYFI_CLIENT_ID else 'NOT CONFIGURED'}")
    print(f"Veryfi AUTHORIZATION: {'Configured' if config.VERYFI_AUTHORIZATION else 'NOT CONFIGURED'}")
    print(f"ESS Validator token: {'Configured' if config.ESS_VALIDATOR_TOKEN else 'NOT CONFIGURED'}")
    
    # show config warning
    for warning in config.check_config():
        print(warning)
    
    print("=" * 60 + "\n")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        stop_cleanup_service()
