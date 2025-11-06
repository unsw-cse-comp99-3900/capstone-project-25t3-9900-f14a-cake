"""Main Flask application"""
from flask import Flask, jsonify
from flask_cors import CORS
import os
import config
from routes.ocr_routes import ocr_bp
from routes.xml_routes import xml_bp
from routes.email_routes import email_bp

app = Flask(__name__)
CORS(app)

# 创建上传文件夹
if not os.path.exists(config.UPLOAD_FOLDER):
    os.makedirs(config.UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_FILE_SIZE_MB * 1024 * 1024

# 注册蓝图
app.register_blueprint(ocr_bp, url_prefix='/api')
app.register_blueprint(xml_bp, url_prefix='/api')
app.register_blueprint(email_bp, url_prefix='/api')


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({'status': 'ok', 'message': 'API is running'})


if __name__ == '__main__':
    # 显示配置警告
    for warning in config.check_config():
        print(warning)
    
    print("=" * 60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
