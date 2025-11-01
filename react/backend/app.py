from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)


CORS(app)

@app.route("/api/health")
def health_check():
    """
    一个简单的健康检查 API 端点。
    """
    # 返回一个 JSON 响应
    return jsonify({"status": "backend_ok"})

