"""XML validation service using ESS Schematron API"""
import base64
import requests
import hashlib


def validate_xml_with_token(xml_content, token):
    """
    使用指定token验证XML
    返回: (success, results, status_code)
    """
    url = "https://services.ebusiness-cloud.com/ess-schematron/v1/api/validate"

    # Base64编码和MD5校验
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

    # 需要验证的两个规则
    rules_to_validate = ['AUNZ_UBL_1_0_10', 'AUNZ_PEPPOL_1_0_10']

    validation_results = {}
    all_successful = True
    first_status_code = None

    for rule in rules_to_validate:
        params = {"rules": [rule]}

        print(f"Validating against rule: {rule}")
        response = requests.post(url, headers=headers, params=params, json=payload, timeout=60)

        # 记录第一个请求的状态码（用于检测401）
        if first_status_code is None:
            first_status_code = response.status_code

        # 如果是401，立即返回（token过期）
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
                'response_body': error_data  # 保存错误响应体
            }
            all_successful = False
            continue

        data = response.json()
        
        # 检查验证结果
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
            'response_body': data  # 保存完整的响应体供用户查看和下载
        }

        if not is_successful:
            all_successful = False

    return all_successful, validation_results, first_status_code


def validate_xml(xml_content, token, token_manager=None):
    """
    验证XML文件是否符合AUNZ规则（支持自动token刷新）
    """
    # 首次验证
    success, results, status_code = validate_xml_with_token(xml_content, token)

    # 如果token过期且提供了token_manager，尝试刷新
    if status_code == 401 and token_manager:
        print("[Validator] Token expired (401), attempting to refresh...")

        try:
            new_token = token_manager.refresh_token()
            print("[Validator] Token refreshed, retrying validation...")

            # 使用新token重试
            success, results, status_code = validate_xml_with_token(xml_content, new_token)

            # 标记token已刷新
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

    # 如果仍然是401，返回错误
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
