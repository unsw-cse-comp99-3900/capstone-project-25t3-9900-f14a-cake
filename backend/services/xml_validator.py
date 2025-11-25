"""XML validation service using ESS Schematron API"""
import base64
import requests
import hashlib


def validate_xml_with_token(xml_content: str, token: str) -> tuple:
    """
    Validate XML using specified token.
    
    Args:
        xml_content: XML content string
        token: ESS Validator access token
    
    Returns:
        Tuple of (success: bool, results: dict, status_code: int)
    """
    url = "https://services.ebusiness-cloud.com/ess-schematron/v1/api/validate"

    # Base64 encode and MD5 checksum
    xml_bytes = xml_content.encode('utf-8')
    base64_content = base64.b64encode(xml_bytes).decode('utf-8')
    checksum_md5 = hashlib.md5(base64_content.encode('utf-8')).hexdigest()

    payload = {
        "filename": "invoice.xml",
        "content": base64_content,
        "checksum": checksum_md5
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Two rules to validate
    rules_to_validate = ['AUNZ_UBL_1_0_10', 'AUNZ_PEPPOL_1_0_10']

    validation_results = {}
    all_successful = True
    first_status_code = None

    for rule in rules_to_validate:
        params = {"rules": [rule]}

        print(f"Validating against rule: {rule}")
        response = requests.post(url, headers=headers, params=params, json=payload, timeout=60)

        # Record first request status code (for 401 detection)
        if first_status_code is None:
            first_status_code = response.status_code

        # If 401, return immediately (token expired)
        if response.status_code == 401:
            return False, {'token_expired': True}, 401

        if response.status_code != 200:
            try:
                error_data = response.json()
            except:
                error_data = {'error': response.text}
            
            validation_results[rule] = {
                'successful': False,
                'status_code': response.status_code,
                'error': response.text,
                'message': f'Validation failed with status {response.status_code}',
                'response_body': error_data  # Save error response body
            }
            all_successful = False
            continue

        data = response.json()
        
        # Check validation result
        is_successful = (
            data.get('successful', False) and
            data.get('report', {}).get('successful', False) and
            data.get('report', {}).get('reports', {}).get(rule, {}).get('successful', False)
        )
        
        validation_results[rule] = {
            'successful': is_successful,
            'status_code': 200,
            'message': data.get('message', ''),
            'assertion_errors_count': data.get('report', {}).get('firedAssertionErrorsCount', 0),
            'reports_count': data.get('report', {}).get('firedSuccessfulReportsCount', 0),
            'response_body': data  # Save complete response body for user viewing and download
        }

        if not is_successful:
            all_successful = False

    return all_successful, validation_results, first_status_code


def validate_xml(xml_content: str, token: str, token_manager=None) -> dict:
    """
    Validate XML file against AUNZ rules (supports automatic token refresh).
    
    Args:
        xml_content: XML content string
        token: ESS Validator access token
        token_manager: Optional TokenManager instance for automatic token refresh
    
    Returns:
        Dictionary with 'success' (bool) and 'results' (dict) keys
    """
    # Initial validation
    success, results, status_code = validate_xml_with_token(xml_content, token)

    # If token expired and token_manager provided, try refreshing
    if status_code == 401 and token_manager:
        print("[Validator] Token expired (401), attempting to refresh...")

        try:
            new_token = token_manager.refresh_token()
            print("[Validator] Token refreshed, retrying validation...")

            # Retry with new token
            success, results, status_code = validate_xml_with_token(xml_content, new_token)

            # Mark token as refreshed
            if status_code != 401:
                results['token_refreshed'] = True

        except Exception as e:
            print(f"[Validator] Failed to refresh token: {str(e)}")
            return {
                'success': False,
                'error': 'Token refresh failed',
                'details': str(e),
                'results': {}
            }

    # If still 401, return error
    if status_code == 401:
        return {
            'success': False,
            'error': 'Authentication failed',
            'details': 'ESS Validator token is expired or invalid. Please update your credentials.',
            'results': {}
        }

    return {
        'success': success,
        'results': results
    }
