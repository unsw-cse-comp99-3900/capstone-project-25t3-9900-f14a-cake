"""Utility functions"""


def allowed_file(filename, allowed_extensions):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed_extensions


def get_mailgun_error_message(status_code, response_text):
    """
    根据Mailgun状态码返回友好的错误信息
    
    参考: https://documentation.mailgun.com/en/latest/api-intro.html#errors
    """
    error_messages = {
        400: {
            'title': 'Bad Request',
            'message': 'The request was invalid. Please check the email address and try again.',
            'details': 'Response typically contains a JSON "message" key with human-readable error details.'
        },
        401: {
            'title': 'Unauthorized',
            'message': 'Invalid or missing API key. Please contact the administrator.',
            'details': 'Check that your API key is correct and properly formatted in the Authorization header.'
        },
        403: {
            'title': 'Forbidden',
            'message': 'Valid credentials but access denied. You may not have permission to send to this email address.',
            'details': 'Ensure you have permissions for the requested resource. Check authorized recipients in Mailgun dashboard.'
        },
        404: {
            'title': 'Not Found',
            'message': 'The requested resource was not found. This may be a temporary system issue.',
            'details': 'Resource not found. Missing JSON response usually indicates incorrect endpoint.'
        },
        429: {
            'title': 'Rate Limited',
            'message': 'Rate limits exceeded. Please retry later.',
            'details': 'Contact support if limits need adjustment.'
        },
        500: {
            'title': 'Internal Error',
            'message': 'Mailgun server error. Please retry with exponential backoff.',
            'details': 'Contact support if the issue persists.'
        }
    }
    
    error_info = error_messages.get(status_code, {
        'title': f'Error {status_code}',
        'message': 'An unexpected error occurred while sending the email.',
        'details': response_text
    })
    
    return error_info
