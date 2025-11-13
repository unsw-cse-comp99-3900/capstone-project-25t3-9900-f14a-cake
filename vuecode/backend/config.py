"""Application configuration"""
import os
from dotenv import load_dotenv

# load env
load_dotenv()

# upload config
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '10'))

# file config
FILE_MAX_AGE_MINUTES = int(os.getenv('FILE_MAX_AGE_MINUTES', '30'))
FILE_CLEANUP_INTERVAL_MINUTES = int(os.getenv('FILE_CLEANUP_INTERVAL_MINUTES', '5'))

# Veryfi API 
VERYFI_CLIENT_ID = os.getenv('VERYFI_CLIENT_ID')
VERYFI_AUTHORIZATION = os.getenv('VERYFI_AUTHORIZATION')


_legacy_username = os.getenv('VERYFI_USERNAME')
_legacy_api_key = os.getenv('VERYFI_API_KEY')
if not VERYFI_AUTHORIZATION and _legacy_username and _legacy_api_key:
    VERYFI_AUTHORIZATION = f"apikey {_legacy_username}:{_legacy_api_key}"

# ESS Validator API 
ESS_VALIDATOR_TOKEN = os.getenv('ESS_VALIDATOR_TOKEN')

# Mailgun config
MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN')
MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
MAILGUN_FROM_EMAIL = os.getenv('MAILGUN_FROM_EMAIL', f'E-Invoice <noreply@{MAILGUN_DOMAIN}>')

# check config
def check_config():
    """检查必要的配置是否存在"""
    warnings = []
    
    if not all([VERYFI_CLIENT_ID, VERYFI_AUTHORIZATION]):
        warnings.append("WARNING: Veryfi API credentials are not fully configured in the .env file")
    
    if not ESS_VALIDATOR_TOKEN:
        warnings.append("WARNING: ESS Validator token is missing (will be auto-generated)")
    
    if not all([MAILGUN_DOMAIN, MAILGUN_API_KEY]):
        warnings.append("WARNING: Mailgun credentials are not configured (email sending will not work)")
    
    return warnings

