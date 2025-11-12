"""XML generation and validation routes"""
from flask import Blueprint, request, jsonify, current_app, send_file
from services.xml_generator import generate_ubl_xml
from services.xml_validator import validate_xml
from services.token_manager import get_token_manager
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import config

xml_bp = Blueprint('xml', __name__)


@xml_bp.route('/upload-xml', methods=['POST'])
def handle_upload_xml():
    """上传XML文件用于验证"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # 检查文件类型
        if not file.filename.lower().endswith('.xml'):
            return jsonify({
                'error': 'Invalid file type',
                'message': 'Only XML files are supported for validation.'
            }), 400
        
        # 读取XML内容
        xml_content = file.read().decode('utf-8')
        
        # 保存文件（带时间戳）
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = os.path.splitext(filename)[0]
        saved_filename = f"{base_name}_{timestamp}.xml"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], saved_filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print(f"SUCCESS: XML file uploaded: {saved_filename}")
        
        return jsonify({
            'success': True,
            'xml_content': xml_content,
            'filename': saved_filename,
            'file_created_at': int(datetime.now().timestamp()),
            'message': 'XML file uploaded successfully'
        })
        
    except UnicodeDecodeError:
        return jsonify({
            'error': 'Invalid XML file',
            'message': 'The file cannot be decoded as UTF-8. Please ensure it is a valid XML file.'
        }), 400
    except Exception as e:
        print(f"Error uploading XML: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@xml_bp.route('/generate-xml', methods=['POST'])
def handle_generate_xml():
    """根据表单数据生成UBL XML格式的发票"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # 生成XML
        xml_content = generate_ubl_xml(data)
        
        # 保存XML文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        xml_filename = f"invoice_{timestamp}.xml"
        xml_path = os.path.join(current_app.config['UPLOAD_FOLDER'], xml_filename)
        
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


@xml_bp.route('/validate-xml', methods=['POST'])
def handle_validate_xml():
    """验证XML发票（两个规则都要通过，支持自动token刷新）"""
    try:
        data = request.get_json()
        
        if not data or 'xml_content' not in data:
            return jsonify({'error': 'No XML content provided'}), 400
        
        xml_content = data['xml_content']
        
        # 获取token manager
        token_manager = get_token_manager()
        
        # 获取当前有效的token
        try:
            current_token = token_manager.get_token()
        except Exception as e:
            print(f"Failed to get token: {str(e)}")
            # 如果自动获取失败，尝试使用环境变量中的token
            current_token = config.ESS_VALIDATOR_TOKEN
            if not current_token:
                return jsonify({
                    'error': 'ESS Validator token not available',
                    'details': 'Failed to obtain authentication token. Please check your configuration.'
                }), 500
        
        # 调用验证服务（传入token_manager以支持自动刷新）
        result = validate_xml(xml_content, current_token, token_manager)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error validating XML: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@xml_bp.route('/download-json/<filename>', methods=['GET'])
def handle_download_json(filename):
    """下载OCR生成的JSON文件"""
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({
                'error': 'File not found',
                'message': 'The file has been deleted (files are auto-deleted after 30 minutes). Please re-upload and process the document.'
            }), 404
        
        return send_file(
            file_path,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        return jsonify({'error': str(e)}), 500
