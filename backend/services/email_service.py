"""Email sending service using Mailgun API"""
import requests
import os


def send_invoice_email(xml_filepath: str, recipient_email: str, mailgun_domain: str, mailgun_api_key: str, from_email: str) -> tuple:
    """
    Send XML invoice via Mailgun API.
    
    Args:
        xml_filepath: Path to XML file
        recipient_email: Recipient email address
        mailgun_domain: Mailgun domain
        mailgun_api_key: Mailgun API key
        from_email: Sender email address
    
    Returns:
        Tuple of (success: bool, message: str, response_data: dict or None)
    """
    
    # Check if file exists
    if not os.path.exists(xml_filepath):
        return False, f"XML file not found: {xml_filepath}", None
    
    try:
        # Read XML file
        with open(xml_filepath, 'rb') as xml_file:
            filename = os.path.basename(xml_filepath)
            
            # Prepare attachment
            files = [
                ('attachment', (filename, xml_file, 'application/xml'))
            ]
            
            # Email content
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
            
            # Send request
            print(f"[EmailService] Sending invoice to {recipient_email}...")
            response = requests.post(
                f"https://api.mailgun.net/v3/{mailgun_domain}/messages",
                auth=('api', mailgun_api_key),
                data=data,
                files=files,
                timeout=30
            )
            
            # Parse response
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
                
                # Return detailed error information based on status code
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


def send_verification_email(recipient_email: str, verification_code: str, mailgun_domain: str, mailgun_api_key: str, from_email: str) -> tuple:
    """
    Send verification code email using Mailgun.
    
    Args:
        recipient_email: Recipient email address
        verification_code: 6-digit verification code
        mailgun_domain: Mailgun domain
        mailgun_api_key: Mailgun API key
        from_email: From email address
    
    Returns:
        Tuple of (success: bool, message: str, response_data: dict or None)
    """
    try:
        # Email content
        data = {
            'from': from_email,
            'to': recipient_email,
            'subject': 'E-Invoice Creator - Email Verification Code',
            'text': (
                f'Dear User,\n\n'
                f'Your email verification code is: {verification_code}\n\n'
                f'This code will expire in 2 minutes.\n\n'
                f'If you did not request this code, please ignore this email.\n\n'
                f'Best regards,\n'
                f'E-Invoice Creator System'
            ),
            'html': (
                f'<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">'
                f'<h2 style="color: #10b981;">Email Verification</h2>'
                f'<p>Dear User,</p>'
                f'<p>Your email verification code is:</p>'
                f'<div style="background-color: #f1f5f9; border: 2px solid #10b981; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">'
                f'<h1 style="color: #10b981; font-size: 32px; letter-spacing: 4px; margin: 0;">{verification_code}</h1>'
                f'</div>'
                f'<p style="color: #6b7280; font-size: 0.9em;">This code will expire in 2 minutes.</p>'
                f'<p style="color: #6b7280; font-size: 0.9em;">If you did not request this code, please ignore this email.</p>'
                f'<p style="color: #6b7280; font-size: 0.9em; margin-top: 30px;">Best regards,<br>E-Invoice Creator System</p>'
                f'</div>'
            )
        }
        
        # Send request
        print(f"[EmailService] Sending verification code to {recipient_email}...")
        response = requests.post(
            f"https://api.mailgun.net/v3/{mailgun_domain}/messages",
            auth=('api', mailgun_api_key),
            data=data,
            timeout=30
        )
        
        # Parse response
        try:
            response_data = response.json()
        except:
            response_data = {'error': response.text}
        
        if response.ok:
            print(f"[EmailService] Verification email sent successfully! Message ID: {response_data.get('id', 'N/A')}")
            return True, f"Verification code sent to {recipient_email}", response_data
        else:
            print(f"[EmailService] Failed to send verification email: {response.status_code}")
            print(f"[EmailService] Response: {response.text}")
            
            # Get error message
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

