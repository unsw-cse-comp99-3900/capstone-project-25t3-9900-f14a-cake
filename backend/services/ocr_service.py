"""OCR service using Veryfi API"""
import base64
import requests
import json
import os
from datetime import datetime
from werkzeug.utils import secure_filename


def extract_invoice_fields(ocr_data: dict) -> dict:
    """
    Extract key invoice fields from OCR data.
    
    Processes OCR response from Veryfi API and extracts structured invoice
    information including invoice details, supplier/customer info, line items,
    and summary amounts.
    
    Args:
        ocr_data: Dictionary containing OCR response data from Veryfi API
    
    Returns:
        Dictionary containing structured invoice data with keys:
        - invoice_info: Basic invoice information (number, dates, currency)
        - supplier: Supplier information (name, address, ABN)
        - customer: Customer information (name, address, ABN)
        - line_items: List of invoice line items
        - summary: Summary amounts (subtotal, tax, total)
    
    Example:
        >>> ocr_data = {'date': '2024-01-01 10:00:00', 'invoice_number': 'INV-001'}
        >>> result = extract_invoice_fields(ocr_data)
        >>> print(result['invoice_info']['invoice_number'])
        'INV-001'
    """
    try:
        # Extract basic invoice information
        issue_date = ocr_data.get('date', '')
        if issue_date and ' ' in issue_date:
            issue_date = issue_date.split(' ')[0]  # Remove time component
        
        due_date = ocr_data.get('due_date', '')
        if due_date and ' ' in due_date:
            due_date = due_date.split(' ')[0]  # Remove time component
        
        invoice_info = {
            'invoice_number': ocr_data.get('invoice_number', ''),
            'issue_date': issue_date,
            'due_date': due_date,
            'currency_code': ocr_data.get('currency_code', 'AUD'),
            'buyer_reference': 'N/A'
        }
        
        # Extract supplier information from vendor field
        vendor = ocr_data.get('vendor', {})
        supplier_info = {
            'name': vendor.get('raw_name', '') or vendor.get('name', ''),
            'street_name': '',  # To be filled by user
            'city_name': '',    # To be filled by user
            'postal_zone': '',  # To be filled by user
            'abn': vendor.get('abn_number', ''),
            'raw_address': vendor.get('raw_address', '') or vendor.get('address', ''),
            'parsed_address': vendor.get('parsed_address', {})
        }
        
        # Extract customer information from bill_to field
        bill_to = ocr_data.get('bill_to', {})
        customer_info = {
            'name': bill_to.get('name', ''),
            'street_name': '',  # To be filled by user
            'city_name': '',    # To be filled by user
            'postal_zone': '',  # To be filled by user
            'abn': bill_to.get('abn_number', ''),
            'raw_address': bill_to.get('address', ''),
            'parsed_address': bill_to.get('parsed_address', {})
        }
        
        # Extract line items from line_items field
        line_items = []
        raw_items = ocr_data.get('line_items', [])
        for item in raw_items:

            description = item.get('full_description', '') or item.get('description', '')

            
            line_items.append({
                'name': description,
                'quantity': float(item.get('quantity', 1.0)),
                'unit_code': 'EA',
                'unit_price': float(item.get('price', 0.0)),
                'line_total': float(item.get('total', 0.0)),
                'tax_percent': None
            })
        
        # Create empty line item if none exist
        if not line_items:
            line_items.append({
                'name': '',
                'quantity': 1.0,
                'unit_code': 'EA',
                'unit_price': 0.0,
                'line_total': 0.0,
                'tax_percent': None
            })
        
        # Calculate summary amounts
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


def process_ocr(file, client_id: str, authorization: str, upload_folder: str) -> tuple:
    """
    Process OCR request using Veryfi API.
    
    Uploads a file to Veryfi API for OCR processing, validates the response,
    and saves the result to a JSON file.
    
    Args:
        file: File object to be processed (must have .read() and .filename attributes)
        client_id: Veryfi API client ID
        authorization: Veryfi API authorization header value
        upload_folder: Directory path where OCR results will be saved
    
    Returns:
        Tuple containing:
        - ocr_data: Dictionary with OCR response data
        - result_filename: Name of the saved JSON file
    
    Raises:
        Exception: If Veryfi API request fails (with status_code and veryfi_error attributes)
        ValueError: If document type is not 'invoice'
    
    Example:
        >>> with open('invoice.pdf', 'rb') as f:
        ...     ocr_data, filename = process_ocr(f, 'client_id', 'auth_token', './uploads')
        ...     print(f"Processed: {filename}")
    """
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
        status_code = response.status_code
        error_message = response.text
        
        # Map Veryfi API status codes to friendly error messages
        veryfi_error_messages = {
            400: "Couldn't download file from provided url.",
            403: "Authentication credentials were not provided.",
            404: "Not found.",
            413: "Request body too large.",
            429: "You have been rate limited.",
            499: "Client closed request or lost connection.",
            500: "Unexpected error.",
            503: "Service is temporarily unavailable. Please try again later.",
            504: "Gateway timeout."
        }
        
        # Use mapped message or default error text
        mapped_message = veryfi_error_messages.get(status_code, error_message)
        
        # Create custom exception with status code and message
        error = Exception(mapped_message)
        error.status_code = status_code
        error.veryfi_error = True
        raise error
    
    ocr_data = response.json()
    
    # Validate document type
    document_type = ocr_data.get('document_type', '')
    if document_type != 'invoice':
        raise ValueError(
            f"Document type '{document_type}' is not supported. "
            f"This system only processes invoice documents. "
            f"Please upload a valid invoice file."
        )
    
    # Save result file with timestamp
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

