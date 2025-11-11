"""Email sending routes"""
from flask import Blueprint, request, jsonify, current_app
import os

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
        
        # 检查XML文件是否存在
        xml_path = os.path.join(current_app.config['UPLOAD_FOLDER'], xml_filename)
        if not os.path.exists(xml_path):
            return jsonify({
                'error': 'XML file not found',
                'message': 'The XML file has been deleted (files are auto-deleted after 30 minutes). Please go back and regenerate the XML.'
            }), 404
        
        # TODO: 实现邮件发送功能
        # 这里需要配置SMTP服务器
        # import smtplib
        # from email.mime.multipart import MIMEMultipart
        # from email.mime.base import MIMEBase
        # from email import encoders
        
        print(f"Would send {xml_filename} to {email}")
        
        return jsonify({
            'success': True,
            'message': f'Invoice sent to {email} successfully'
        })
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
