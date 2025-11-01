from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# 指定上传文件夹
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/api/health")
def health_check():
    return jsonify({"status": "backend_ok"})


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """
    接收前端上传的发票文件
    """
    # 检查请求中是否包含文件
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]

    # 检查文件名是否为空
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # 保存文件
    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    return jsonify({
        "message": "File uploaded successfully",
        "filename": file.filename,
        "path": save_path
    }), 200


if __name__ == "__main__":
    # Flask 在容器内监听所有地址（Docker 模式）
    app.run(host="0.0.0.0", port=5001, debug=True)
