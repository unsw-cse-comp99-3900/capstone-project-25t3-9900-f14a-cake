"""Email sending routes"""
from flask import Blueprint, request, jsonify, current_app
from services.email_service import send_invoice_email
import os
import config
import re

email_bp = Blueprint('email', __name__)


def is_valid_email(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


@email_bp.route('/send-email', methods=['POST'])
def handle_send_email():
    """发送XML发票到指定邮箱"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip()
        xml_filename = data.get('xml_filename')
        
        if not email or not xml_filename:
            return jsonify({'error': 'Email and XML filename are required'}), 400
        
        # 验证邮箱格式
        if not is_valid_email(email):
            return jsonify({
                'error': 'Invalid email format',
                'message': 'Please enter a valid email address (e.g., user@example.com)'
            }), 400
        
        # 检查XML文件是否存在
        xml_path = os.path.join(current_app.config['UPLOAD_FOLDER'], xml_filename)
        if not os.path.exists(xml_path):
            return jsonify({
                'error': 'XML file not found',
                'message': 'The XML file has been deleted (files are auto-deleted after 30 minutes). Please go back and regenerate the XML.'
            }), 404
        
        # 检查Mailgun配置
        if not all([config.MAILGUN_DOMAIN, config.MAILGUN_API_KEY]):
            return jsonify({
                'error': 'Email service not configured',
                'message': 'Mailgun credentials are missing. Please contact the administrator.'
            }), 500
        
        # 发送邮件
        success, message, response_data = send_invoice_email(
            xml_filepath=xml_path,
            recipient_email=email,
            mailgun_domain=config.MAILGUN_DOMAIN,
            mailgun_api_key=config.MAILGUN_API_KEY,
            from_email=config.MAILGUN_FROM_EMAIL
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'mailgun_response': response_data
            })
        else:
            # 根据状态码返回适当的HTTP状态
            status_code = response_data.get('status_code', 500) if response_data else 500
            
            return jsonify({
                'error': 'Failed to send email',
                'message': message,
                'error_info': response_data.get('error_info') if response_data else None,
                'details': response_data
            }), status_code
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
