"""XML generation and validation routes"""
from flask import Blueprint, request, jsonify, current_app, send_file
from services.xml_generator import generate_ubl_xml
from services.xml_validator import validate_xml
from datetime import datetime
import os
import config

xml_bp = Blueprint('xml', __name__)


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
    """验证XML发票（两个规则都要通过）"""
    try:
        data = request.get_json()
        
        if not data or 'xml_content' not in data:
            return jsonify({'error': 'No XML content provided'}), 400
        
        xml_content = data['xml_content']
        
        # 检查token
        if not config.ESS_VALIDATOR_TOKEN:
            return jsonify({
                'error': 'ESS Validator token not configured',
                'details': 'Please check your .env file'
            }), 500
        
        # 调用验证服务
        result = validate_xml(xml_content, config.ESS_VALIDATOR_TOKEN)
        
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
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            file_path,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        return jsonify({'error': str(e)}), 500

