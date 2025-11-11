"""Main Flask application"""
from flask import Flask, jsonify
from flask_cors import CORS
import os
import config
from routes.ocr_routes import ocr_bp
from routes.xml_routes import xml_bp
from routes.email_routes import email_bp
from services.file_cleanup import start_cleanup_service, stop_cleanup_service
from services.token_manager import get_token_manager
import atexit

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

# 初始化token manager
token_manager = get_token_manager()

# 启动文件清理服务
cleanup_service = start_cleanup_service(
    upload_folder=config.UPLOAD_FOLDER,
    max_age_minutes=config.FILE_MAX_AGE_MINUTES,
    check_interval_minutes=config.FILE_CLEANUP_INTERVAL_MINUTES
)

# 应用关闭时停止清理服务
atexit.register(stop_cleanup_service)


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({'status': 'ok', 'message': 'API is running'})


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("E-Invoice API Server Starting...")
    print("=" * 60)
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"Allowed file types: {', '.join(sorted(config.ALLOWED_EXTENSIONS))}")
    print(f"Max file size: {config.MAX_FILE_SIZE_MB}MB")
    print(f"Veryfi CLIENT_ID: {'Configured' if config.VERYFI_CLIENT_ID else 'NOT CONFIGURED'}")
    print(f"Veryfi AUTHORIZATION: {'Configured' if config.VERYFI_AUTHORIZATION else 'NOT CONFIGURED'}")
    print(f"ESS Validator token: {'Configured' if config.ESS_VALIDATOR_TOKEN else 'NOT CONFIGURED'}")
    
    # 显示配置警告
    for warning in config.check_config():
        print(warning)
    
    print("=" * 60 + "\n")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        stop_cleanup_service()
