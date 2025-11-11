"""OCR related routes"""
from flask import Blueprint, request, jsonify, current_app
from services.ocr_service import process_ocr, extract_invoice_fields
from utils import allowed_file
import config
import requests

ocr_bp = Blueprint('ocr', __name__)


@ocr_bp.route('/ocr', methods=['POST'])
def handle_ocr():
    """处理上传的文件并通过 Veryfi API 进行 OCR 识别"""
    try:
        # 检查文件上传
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename, config.ALLOWED_EXTENSIONS):
            return jsonify({'error': 'File type not allowed. Only PDF, JPG, and JPEG are supported.'}), 400
        
        # 检查凭证
        if not config.VERYFI_CLIENT_ID or not config.VERYFI_AUTHORIZATION:
            print("ERROR: Veryfi credentials missing!")
            print(f"  CLIENT_ID: {'OK' if config.VERYFI_CLIENT_ID else 'MISSING'}")
            print(f"  AUTHORIZATION: {'OK' if config.VERYFI_AUTHORIZATION else 'MISSING'}")
            return jsonify({
                'error': 'Veryfi API credentials are not configured',
                'details': 'Please check your .env file'
            }), 500
        
        # 调用OCR服务
        ocr_data, result_filename = process_ocr(
            file,
            config.VERYFI_CLIENT_ID,
            config.VERYFI_AUTHORIZATION,
            current_app.config['UPLOAD_FOLDER']
        )
        
        # 提取关键字段
        extracted_data = extract_invoice_fields(ocr_data)
        
        import time
        
        return jsonify({
            'success': True,
            'raw_data': ocr_data,
            'extracted': extracted_data,
            'json_filename': result_filename,
            'file_created_at': int(time.time()),  # 文件创建时间戳（秒）
            'message': 'Document processed successfully'
        })
        
    except ValueError as e:
        # 文档类型错误
        print(f"ERROR: Document type validation failed: {str(e)}")
        return jsonify({
            'error': 'Invalid document type',
            'details': str(e)
        }), 400
    except requests.Timeout:
        print("ERROR: Request timeout")
        return jsonify({'error': 'Request timeout. Please try again.'}), 504
    except Exception as e:
        print(f"ERROR: Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

