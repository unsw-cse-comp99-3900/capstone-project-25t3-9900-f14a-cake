"""XML validation service using ESS Schematron API"""
import base64
import requests
import hashlib


def validate_xml(xml_content, token):
    """
    验证XML文件是否符合AUNZ规则
    返回格式：{
        'success': bool,
        'results': {
            'AUNZ_UBL_1_0_10': {...},
            'AUNZ_PEPPOL_1_0_10': {...}
        }
    }
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
    
    for rule in rules_to_validate:
        params = {"rules": [rule]}
        
        print(f"Validating against rule: {rule}")
        response = requests.post(url, headers=headers, params=params, json=payload, timeout=60)
        
        if response.status_code != 200:
            validation_results[rule] = {
                'successful': False,
                'status_code': response.status_code,
                'error': response.text,
                'message': f'Validation failed with status {response.status_code}'
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
            'data': data,
            'message': data.get('message', ''),
            'assertion_errors_count': data.get('report', {}).get('firedAssertionErrorsCount', 0),
            'reports_count': data.get('report', {}).get('firedSuccessfulReportsCount', 0)
        }
        
        if not is_successful:
            all_successful = False
    
    return {
        'success': all_successful,
        'results': validation_results
    }

