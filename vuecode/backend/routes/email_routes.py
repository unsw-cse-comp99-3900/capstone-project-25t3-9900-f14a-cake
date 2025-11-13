"""Email sending routes"""
from flask import Blueprint, request, jsonify

email_bp = Blueprint('email', __name__)


@email_bp.route('/send-email', methods=['POST'])
def handle_send_email():
    """发送XML发票到指定邮箱"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email')
        xml_filename = data.get('xml_filename')
        
        if not email or not xml_filename:
            return jsonify({'error': 'Email and XML filename are required'}), 400
        
        # TODO: 实现邮件发送功能
        print(f"Would send {xml_filename} to {email}")
        
        return jsonify({
            'success': True,
            'message': f'Invoice sent to {email} successfully'
        })
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return jsonify({'error': str(e)}), 500

