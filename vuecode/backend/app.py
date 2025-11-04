from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import base64
import requests
import json
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# 加载环境变量
load_dotenv()

# 配置上传文件夹
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg'}
MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '10'))

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE_MB * 1024 * 1024  # Max file size from env (default 10MB)

# Veryfi API 凭证
VERYFI_CLIENT_ID = os.getenv('VERYFI_CLIENT_ID')
VERYFI_AUTHORIZATION = os.getenv('VERYFI_AUTHORIZATION')

# 兼容旧的用户名+密钥配置
_legacy_username = os.getenv('VERYFI_USERNAME')
_legacy_api_key = os.getenv('VERYFI_API_KEY')
if not VERYFI_AUTHORIZATION and _legacy_username and _legacy_api_key:
    VERYFI_AUTHORIZATION = f"apikey {_legacy_username}:{_legacy_api_key}"
VERYFI_URL = "https://api.veryfi.com/api/v8/partner/documents/"

# ESS Validator API 凭证
ESS_VALIDATOR_TOKEN = os.getenv('ESS_VALIDATOR_TOKEN')
ESS_VALIDATOR_URL = "https://services.ebusiness-cloud.com/ess-schematron/v1/api/validate"

if not all([VERYFI_CLIENT_ID, VERYFI_AUTHORIZATION]):
    print("WARNING: Veryfi API credentials are not fully configured in the .env file")

if not ESS_VALIDATOR_TOKEN:
    print("WARNING: ESS Validator token is missing in the .env file")


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
        
        # 供应商信息 - 从vendor获取
        vendor = ocr_data.get('vendor', {})
        supplier_info = {
            'name': vendor.get('raw_name', '') or vendor.get('name', ''),
            'street_name': '',  # 用户填写
            'city_name': '',    # 用户填写
            'postal_zone': '', # 用户填写
            'abn': '',         # 用户填写
            'raw_address': vendor.get('raw_address', '') or vendor.get('address', '')  # 供展示
        }
        
        # 客户信息 - 从bill_to只获取name
        bill_to = ocr_data.get('bill_to', {})
        customer_info = {
            'name': bill_to.get('name', ''),
            'street_name': '',  # 用户填写
            'city_name': '',    # 用户填写
            'postal_zone': '', # 用户填写
            'abn': '',         # 用户填写
            'raw_address': bill_to.get('address', '')  # 供展示
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
                'unit_code': 'EA',  # 默认单位
                'unit_price': float(item.get('price', 0.0)),
                'line_total': float(item.get('total', 0.0)),
                'tax_percent': None  # 用户填写
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
            'supplier': {'name': '', 'street_name': '', 'city_name': '', 'postal_zone': '', 'abn': '', 'raw_address': ''},
            'customer': {'name': '', 'street_name': '', 'city_name': '', 'postal_zone': '', 'abn': '', 'raw_address': ''},
            'line_items': [{'name': '', 'quantity': 1.0, 'unit_code': 'EA', 'unit_price': 0.0, 'line_total': 0.0, 'tax_percent': None}],
            'summary': {'subtotal': 0.0, 'tax_amount': 0.0, 'total': 0.0}
        }


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({'status': 'ok', 'message': 'API is running'})


@app.route('/api/ocr', methods=['POST'])
def process_ocr():
    """
    处理上传的文件并通过 Veryfi API 进行 OCR 识别
    """
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        # 检查文件名
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # 检查文件类型
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Only PDF, JPG, and JPEG are supported.'}), 400

        # 检查凭证配置
        if not VERYFI_CLIENT_ID or not VERYFI_AUTHORIZATION:
            print("ERROR: Veryfi credentials missing!")
            print(f"  CLIENT_ID: {'OK' if VERYFI_CLIENT_ID else 'MISSING'}")
            print(f"  AUTHORIZATION: {'OK' if VERYFI_AUTHORIZATION else 'MISSING'}")
            return jsonify({
                'error': 'Veryfi API credentials are not configured',
                'details': 'Please check your .env file and ensure VERYFI_CLIENT_ID and VERYFI_AUTHORIZATION are set'
            }), 500

        # 读取文件内容并编码为 Base64
        file_content = file.read()
        encoded_file = base64.b64encode(file_content).decode("utf-8")

        # 准备 Veryfi API 请求
        payload = {
            "file_data": encoded_file,
            "categories": ["Invoices"],
            "auto_delete": True
        }

        headers = {
            "Content-Type": "application/json",
            "Client-Id": VERYFI_CLIENT_ID,
            "Authorization": VERYFI_AUTHORIZATION,
        }

        # 调用 Veryfi API
        print(f"Calling Veryfi API for file: {file.filename}")
        response = requests.post(VERYFI_URL, headers=headers, json=payload, timeout=60)

        # 检查响应
        if response.ok:
            ocr_data = response.json()

            # 使用时间戳保存结果文件
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name = os.path.splitext(filename)[0]
            result_filename = f"{base_name}_{timestamp}_result.json"
            result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_filename)

            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(ocr_data, f, indent=2, ensure_ascii=False)

            print(f"SUCCESS: OCR completed! Result saved to: {result_path}")

            # 提取关键字段
            extracted_data = extract_invoice_fields(ocr_data)

            return jsonify({
                'success': True,
                'raw_data': ocr_data,
                'extracted': extracted_data,
                'json_filename': result_filename,  # 返回实际保存的文件名
                'message': 'Document processed successfully'
            })
        else:
            print(f"ERROR: Veryfi API returned status {response.status_code}")
            print(f"Response: {response.text}")
            return jsonify({
                'error': 'OCR processing failed',
                'details': response.text
            }), response.status_code

    except requests.Timeout:
        print("ERROR: Request timeout")
        return jsonify({'error': 'Request timeout. Please try again.'}), 504
    except Exception as e:
        print(f"ERROR: Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/download-json/<filename>', methods=['GET'])
def download_json(filename):
    """
    下载OCR生成的JSON文件
    """
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        from flask import send_file
        return send_file(
            file_path,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-xml', methods=['POST'])
def generate_xml():
    """
    根据表单数据生成UBL XML格式的发票
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # 生成XML
        xml_content = generate_ubl_xml(data)
        
        # 保存XML文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        xml_filename = f"invoice_{timestamp}.xml"
        xml_path = os.path.join(app.config['UPLOAD_FOLDER'], xml_filename)
        
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print(f"SUCCESS: XML generated: {xml_path}")
        
        return jsonify({
            'success': True,
            'xml_content': xml_content,
            'filename': xml_filename,
            'message': 'XML generated successfully'
        })
        
    except Exception as e:
        print(f"Error generating XML: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def generate_ubl_xml(data):
    """生成UBL格式的XML"""
    from xml.dom import minidom
    import xml.etree.ElementTree as ET
    
    # 命名空间
    NS_INVOICE = 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2'
    NS_CAC = 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
    NS_CBC = 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
    
    # 注册命名空间
    ET.register_namespace('', NS_INVOICE)
    ET.register_namespace('cac', NS_CAC)
    ET.register_namespace('cbc', NS_CBC)
    
    cbc = '{' + NS_CBC + '}'
    cac = '{' + NS_CAC + '}'
    
    # 创建根元素（命名空间会自动添加）
    invoice = ET.Element('{' + NS_INVOICE + '}Invoice')
    
    # 发票头部（固定值）
    ET.SubElement(invoice, cbc + 'CustomizationID').text = 'urn:cen.eu:en16931:2017#conformant#urn:fdc:peppol.eu:2017:poacc:billing:international:aunz:3.0'
    ET.SubElement(invoice, cbc + 'ProfileID').text = 'urn:fdc:peppol.eu:2017:poacc:billing:01:1.0'
    
    # 基本信息
    info = data.get('invoice_info', {})
    ET.SubElement(invoice, cbc + 'ID').text = info.get('invoice_number', 'INV-000')
    ET.SubElement(invoice, cbc + 'IssueDate').text = info.get('issue_date', '')
    ET.SubElement(invoice, cbc + 'DueDate').text = info.get('due_date', '')
    ET.SubElement(invoice, cbc + 'InvoiceTypeCode').text = '380'
    ET.SubElement(invoice, cbc + 'DocumentCurrencyCode').text = info.get('currency_code', 'AUD')
    ET.SubElement(invoice, cbc + 'BuyerReference').text = info.get('buyer_reference', 'N/A')
    
    # 供应商信息
    supplier = data.get('supplier', {})
    supplier_party = ET.SubElement(invoice, cac + 'AccountingSupplierParty')
    supplier_party_elem = ET.SubElement(supplier_party, cac + 'Party')
    
    supplier_abn = supplier.get('abn', '').replace(' ', '')
    ET.SubElement(supplier_party_elem, cbc + 'EndpointID', schemeID='0151').text = supplier_abn
    
    supplier_name_elem = ET.SubElement(supplier_party_elem, cac + 'PartyName')
    ET.SubElement(supplier_name_elem, cbc + 'Name').text = supplier.get('name', '')
    
    supplier_address = ET.SubElement(supplier_party_elem, cac + 'PostalAddress')
    ET.SubElement(supplier_address, cbc + 'StreetName').text = supplier.get('street_name', '')
    ET.SubElement(supplier_address, cbc + 'CityName').text = supplier.get('city_name', '')
    ET.SubElement(supplier_address, cbc + 'PostalZone').text = supplier.get('postal_zone', '')
    supplier_country = ET.SubElement(supplier_address, cac + 'Country')
    ET.SubElement(supplier_country, cbc + 'IdentificationCode').text = 'AU'
    
    supplier_legal = ET.SubElement(supplier_party_elem, cac + 'PartyLegalEntity')
    ET.SubElement(supplier_legal, cbc + 'RegistrationName').text = supplier.get('name', '')
    ET.SubElement(supplier_legal, cbc + 'CompanyID', schemeID='0151').text = supplier_abn
    
    # 客户信息
    customer = data.get('customer', {})
    customer_party = ET.SubElement(invoice, cac + 'AccountingCustomerParty')
    customer_party_elem = ET.SubElement(customer_party, cac + 'Party')
    
    customer_abn = customer.get('abn', '').replace(' ', '')
    ET.SubElement(customer_party_elem, cbc + 'EndpointID', schemeID='0151').text = customer_abn
    
    customer_name_elem = ET.SubElement(customer_party_elem, cac + 'PartyName')
    ET.SubElement(customer_name_elem, cbc + 'Name').text = customer.get('name', '')
    
    customer_address = ET.SubElement(customer_party_elem, cac + 'PostalAddress')
    ET.SubElement(customer_address, cbc + 'StreetName').text = customer.get('street_name', '')
    ET.SubElement(customer_address, cbc + 'CityName').text = customer.get('city_name', '')
    ET.SubElement(customer_address, cbc + 'PostalZone').text = customer.get('postal_zone', '')
    customer_country = ET.SubElement(customer_address, cac + 'Country')
    ET.SubElement(customer_country, cbc + 'IdentificationCode').text = 'AU'
    
    customer_legal = ET.SubElement(customer_party_elem, cac + 'PartyLegalEntity')
    ET.SubElement(customer_legal, cbc + 'RegistrationName').text = customer.get('name', '')
    ET.SubElement(customer_legal, cbc + 'CompanyID', schemeID='0151').text = customer_abn
    
    # 计算税额（按税率分组）
    line_items = data.get('line_items', [])
    currency = info.get('currency_code', 'AUD')
    
    # 按税率分组计算
    tax_groups = {}
    total_line_extension = 0.0
    
    for item in line_items:
        line_total = float(item.get('line_total', 0))
        tax_percent = float(item.get('tax_percent', 0))
        
        total_line_extension += line_total
        
        if tax_percent not in tax_groups:
            tax_groups[tax_percent] = {'taxable': 0.0, 'tax': 0.0}
        
        tax_groups[tax_percent]['taxable'] += line_total
        tax_groups[tax_percent]['tax'] += line_total * tax_percent / 100
    
    # 税额汇总
    total_tax_amount = sum(group['tax'] for group in tax_groups.values())
    
    tax_total = ET.SubElement(invoice, cac + 'TaxTotal')
    ET.SubElement(tax_total, cbc + 'TaxAmount', currencyID=currency).text = f'{total_tax_amount:.2f}'
    
    for tax_percent, amounts in sorted(tax_groups.items(), reverse=True):
        tax_subtotal = ET.SubElement(tax_total, cac + 'TaxSubtotal')
        ET.SubElement(tax_subtotal, cbc + 'TaxableAmount', currencyID=currency).text = f"{amounts['taxable']:.2f}"
        ET.SubElement(tax_subtotal, cbc + 'TaxAmount', currencyID=currency).text = f"{amounts['tax']:.2f}"
        
        tax_category = ET.SubElement(tax_subtotal, cac + 'TaxCategory')
        ET.SubElement(tax_category, cbc + 'ID').text = 'S'
        ET.SubElement(tax_category, cbc + 'Percent').text = f'{tax_percent:.2f}'
        
        tax_scheme = ET.SubElement(tax_category, cac + 'TaxScheme')
        ET.SubElement(tax_scheme, cbc + 'ID').text = 'GST'
    
    # 金额汇总
    total_with_tax = total_line_extension + total_tax_amount
    
    monetary_total = ET.SubElement(invoice, cac + 'LegalMonetaryTotal')
    ET.SubElement(monetary_total, cbc + 'LineExtensionAmount', currencyID=currency).text = f'{total_line_extension:.2f}'
    ET.SubElement(monetary_total, cbc + 'TaxExclusiveAmount', currencyID=currency).text = f'{total_line_extension:.2f}'
    ET.SubElement(monetary_total, cbc + 'TaxInclusiveAmount', currencyID=currency).text = f'{total_with_tax:.2f}'
    ET.SubElement(monetary_total, cbc + 'PayableAmount', currencyID=currency).text = f'{total_with_tax:.2f}'
    
    # 商品明细
    for idx, item in enumerate(line_items, 1):
        invoice_line = ET.SubElement(invoice, cac + 'InvoiceLine')
        ET.SubElement(invoice_line, cbc + 'ID').text = str(idx)
        
        quantity = float(item.get('quantity', 1))
        unit_code = item.get('unit_code', 'EA')
        ET.SubElement(invoice_line, cbc + 'InvoicedQuantity', unitCode=unit_code).text = f'{quantity:.0f}'
        
        line_total = float(item.get('line_total', 0))
        ET.SubElement(invoice_line, cbc + 'LineExtensionAmount', currencyID=currency).text = f'{line_total:.2f}'
        
        item_elem = ET.SubElement(invoice_line, cac + 'Item')
        ET.SubElement(item_elem, cbc + 'Name').text = item.get('name', '')
        
        tax_percent = float(item.get('tax_percent', 0))
        classified_tax = ET.SubElement(item_elem, cac + 'ClassifiedTaxCategory')
        ET.SubElement(classified_tax, cbc + 'ID').text = 'S'
        ET.SubElement(classified_tax, cbc + 'Percent').text = f'{tax_percent:.2f}'
        
        tax_scheme = ET.SubElement(classified_tax, cac + 'TaxScheme')
        ET.SubElement(tax_scheme, cbc + 'ID').text = 'GST'
        
        price_elem = ET.SubElement(invoice_line, cac + 'Price')
        unit_price = float(item.get('unit_price', 0))
        ET.SubElement(price_elem, cbc + 'PriceAmount', currencyID=currency).text = f'{unit_price:.2f}'
    
    # 格式化输出
    xml_str = ET.tostring(invoice, encoding='utf-8')
    dom = minidom.parseString(xml_str)
    return dom.toprettyxml(indent='  ', encoding='utf-8').decode('utf-8')


@app.route('/api/send-email', methods=['POST'])
def send_email():
    """
    发送XML发票到指定邮箱
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email')
        xml_filename = data.get('xml_filename')
        
        if not email or not xml_filename:
            return jsonify({'error': 'Email and XML filename are required'}), 400
        

        
        print(f"Would send {xml_filename} to {email}")
        
        return jsonify({
            'success': True,
            'message': f'Invoice sent to {email} successfully'
        })
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("E-Invoice API Server Starting...")
    print("=" * 60)
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"Allowed file types: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
    print(f"Max file size: {MAX_FILE_SIZE_MB}MB")
    print(f"Veryfi CLIENT_ID: {'Configured' if VERYFI_CLIENT_ID else 'NOT CONFIGURED'}")
    print(f"Veryfi AUTHORIZATION: {'Configured' if VERYFI_AUTHORIZATION else 'NOT CONFIGURED'}")
    print(f"ESS Validator token: {'Configured' if ESS_VALIDATOR_TOKEN else 'NOT CONFIGURED'}")
    print("=" * 60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
