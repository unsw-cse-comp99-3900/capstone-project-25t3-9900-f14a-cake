"""Email sending service using Mailgun API"""
import requests
import os


def send_invoice_email(xml_filepath, recipient_email, mailgun_domain, mailgun_api_key, from_email):
    """
    使用Mailgun发送XML发票
    
    Args:
        xml_filepath: XML文件路径
        recipient_email: 收件人邮箱
        mailgun_domain: Mailgun域名
        mailgun_api_key: Mailgun API密钥
        from_email: 发件人邮箱
    
    Returns:
        (success: bool, message: str, response_data: dict)
    """
    
    # 检查文件是否存在
    if not os.path.exists(xml_filepath):
        return False, f"XML file not found: {xml_filepath}", None
    
    try:
        # 读取XML文件
        with open(xml_filepath, 'rb') as xml_file:
            filename = os.path.basename(xml_filepath)
            
            # 准备附件
            files = [
                ('attachment', (filename, xml_file, 'application/xml'))
            ]
            
            # 邮件内容
            data = {
                'from': from_email,
                'to': recipient_email,
                'subject': f'E-Invoice: {filename}',
                'text': (
                    f'Dear Customer,\n\n'
                    f'Please find attached the e-invoice XML file: {filename}\n\n'
                    f'This invoice has been validated against AUNZ_UBL and AUNZ_PEPPOL standards.\n\n'
                    f'Best regards,\n'
                    f'E-Invoice Creator System'
                ),
                'html': (
                    f'<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">'
                    f'<h2 style="color: #10b981;">E-Invoice Delivery</h2>'
                    f'<p>Dear Customer,</p>'
                    f'<p>Please find attached the e-invoice XML file: <strong>{filename}</strong></p>'
                    f'<p>This invoice has been validated against:</p>'
                    f'<ul>'
                    f'<li>AUNZ_UBL_1_0_10 ✓</li>'
                    f'<li>AUNZ_PEPPOL_1_0_10 ✓</li>'
                    f'</ul>'
                    f'<p style="color: #6b7280; font-size: 0.9em;">Best regards,<br>E-Invoice Creator System</p>'
                    f'</div>'
                )
            }
            
            # 发送请求
            print(f"[EmailService] Sending invoice to {recipient_email}...")
            response = requests.post(
                f"https://api.mailgun.net/v3/{mailgun_domain}/messages",
                auth=('api', mailgun_api_key),
                data=data,
                files=files,
                timeout=30
            )
            
            # 解析响应
            try:
                response_data = response.json()
            except:
                response_data = {'error': response.text}
            
            if response.ok:
                print(f"[EmailService] Email sent successfully! Message ID: {response_data.get('id', 'N/A')}")
                return True, f"Invoice successfully sent to {recipient_email}", response_data
            else:
                print(f"[EmailService] Failed to send email: {response.status_code}")
                print(f"[EmailService] Response: {response.text}")
                
                # 根据状态码返回详细错误信息
                from utils import get_mailgun_error_message
                error_info = get_mailgun_error_message(response.status_code, response.text)
                
                error_message = f"{error_info['title']}: {error_info['message']}"
                
                return False, error_message, {
                    'status_code': response.status_code,
                    'error_info': error_info,
                    'raw_response': response_data
                }
        
    except requests.Timeout:
        return False, "Request timeout. Please try again.", None
    except Exception as e:
        print(f"[EmailService] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, str(e), None

