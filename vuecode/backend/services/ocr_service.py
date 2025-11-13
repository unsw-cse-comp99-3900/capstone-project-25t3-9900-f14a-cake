"""OCR service using Veryfi API"""
import base64
import requests
import json
import os
from datetime import datetime
from werkzeug.utils import secure_filename


def extract_invoice_fields(ocr_data):
    """从OCR数据中提取关键发票字段"""
    try:
        # 基本信息
        issue_date = ocr_data.get('date', '')
        if issue_date and ' ' in issue_date:
            issue_date = issue_date.split(' ')[0]  # 去除时间部分
        
        due_date = ocr_data.get('due_date', '')
        if due_date and ' ' in due_date:
            due_date = due_date.split(' ')[0]  # 去除时间部分
        
        invoice_info = {
            'invoice_number': ocr_data.get('invoice_number', ''),
            'issue_date': issue_date,
            'due_date': due_date,
            'currency_code': ocr_data.get('currency_code', 'AUD'),
            'buyer_reference': 'N/A'
        }
        
        # 供应商信息 - 从vendor获取，包括parsed_address
        vendor = ocr_data.get('vendor', {})
        supplier_info = {
            'name': vendor.get('raw_name', '') or vendor.get('name', ''),
            'street_name': '',
            'city_name': '',
            'postal_zone': '',
            'abn': '',
            'raw_address': vendor.get('raw_address', '') or vendor.get('address', ''),
            'parsed_address': vendor.get('parsed_address', {})
        }
        
        # 客户信息 - 从bill_to获取，包括parsed_address
        bill_to = ocr_data.get('bill_to', {})
        customer_info = {
            'name': bill_to.get('name', ''),
            'street_name': '',
            'city_name': '',
            'postal_zone': '',
            'abn': '',
            'raw_address': bill_to.get('address', ''),
            'parsed_address': bill_to.get('parsed_address', {})
        }
        
        # 商品明细 - 从line_items提取
        line_items = []
        raw_items = ocr_data.get('line_items', [])
        for item in raw_items:
            # 跳过疑似税费的行
            description = item.get('full_description', '') or item.get('description', '')
            if description and any(keyword in description.upper() for keyword in ['GST', 'TAX', 'TOTAL']):
                continue
            
            line_items.append({
                'name': description,
                'quantity': float(item.get('quantity', 1.0)),
                'unit_code': 'EA',
                'unit_price': float(item.get('price', 0.0)),
                'line_total': float(item.get('total', 0.0)),
                'tax_percent': None
            })
        
        # 如果没有商品，创建一个空的
        if not line_items:
            line_items.append({
                'name': '',
                'quantity': 1.0,
                'unit_code': 'EA',
                'unit_price': 0.0,
                'line_total': 0.0,
                'tax_percent': None
            })
        
        # 金额汇总
        summary = {
            'subtotal': float(ocr_data.get('subtotal', 0.0)),
            'tax_amount': float(ocr_data.get('tax', 0.0)),
            'total': float(ocr_data.get('total', 0.0))
        }
        
        return {
            'invoice_info': invoice_info,
            'supplier': supplier_info,
            'customer': customer_info,
            'line_items': line_items,
            'summary': summary
        }
    except Exception as e:
        print(f"ERROR extracting fields: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'invoice_info': {'invoice_number': '', 'issue_date': '', 'due_date': '', 'currency_code': 'AUD', 'buyer_reference': 'N/A'},
            'supplier': {'name': '', 'street_name': '', 'city_name': '', 'postal_zone': '', 'abn': '', 'raw_address': '', 'parsed_address': {}},
            'customer': {'name': '', 'street_name': '', 'city_name': '', 'postal_zone': '', 'abn': '', 'raw_address': '', 'parsed_address': {}},
            'line_items': [{'name': '', 'quantity': 1.0, 'unit_code': 'EA', 'unit_price': 0.0, 'line_total': 0.0, 'tax_percent': None}],
            'summary': {'subtotal': 0.0, 'tax_amount': 0.0, 'total': 0.0}
        }


def process_ocr(file, client_id, authorization, upload_folder):
    """处理OCR请求"""
    file_content = file.read()
    encoded_file = base64.b64encode(file_content).decode("utf-8")
    
    payload = {
        "file_data": encoded_file,
        "categories": ["Invoices"],
        "auto_delete": True,
        "parse_address": True
    }
    
    headers = {
        "Content-Type": "application/json",
        "Client-Id": client_id,
        "Authorization": authorization,
    }
    
    veryfi_url = "https://api.veryfi.com/api/v8/partner/documents/"
    
    print(f"Calling Veryfi API for file: {file.filename}")
    response = requests.post(veryfi_url, headers=headers, json=payload, timeout=60)
    
    if not response.ok:
        raise Exception(f"Veryfi API error ({response.status_code}): {response.text}")
    
    ocr_data = response.json()
    
    # 验证文档类型
    document_type = ocr_data.get('document_type', '')
    if document_type != 'invoice':
        raise ValueError(
            f"Document type '{document_type}' is not supported. "
            f"This system only processes invoice documents. "
            f"Please upload a valid invoice file."
        )
    
    # 使用时间戳保存结果文件
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name = os.path.splitext(filename)[0]
    result_filename = f"{base_name}_{timestamp}_result.json"
    result_path = os.path.join(upload_folder, result_filename)
    
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(ocr_data, f, indent=2, ensure_ascii=False)
    
    print(f"SUCCESS: OCR completed! Document type: {document_type}")
    print(f"Result saved to: {result_path}")
    
    return ocr_data, result_filename

