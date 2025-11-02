from flask import Flask, jsonify, request
from flask_cors import CORS
import base64
import requests
import json
import os
from json_to_ubl import json_to_ubl_invoice   # ✅ 引入你写的转换函数

app = Flask(__name__)
CORS(app)

# === Veryfi API 配置 ===
CLIENT_ID = 'vrfdpLpaXnU1nGBL5WIU9dyfio1mOS594gtwEoM'
AUTHORIZATION = 'apikey danielxjun:d0d4abc6950a1f487b362fa4f5df3a36'
VERYFI_URL = "https://api.veryfi.com/api/v8/partner/documents/"

# === 上传目录 ===
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/api/health")
def health_check():
    return jsonify({"status": "backend_ok"})


@app.route("/api/upload", methods=["POST"])
def upload_and_parse_invoice():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    try:
        # === Step 1: 调用 Veryfi OCR ===
        with open(save_path, "rb") as f:
            encoded_file = base64.b64encode(f.read()).decode("utf-8")

        payload = {
            "file_data": encoded_file,
            "categories": ["Invoices"],
            "auto_delete": True
        }

        headers = {
            "Content-Type": "application/json",
            "Client-Id": CLIENT_ID,
            "Authorization": AUTHORIZATION,
        }

        resp = requests.post(VERYFI_URL, headers=headers, json=payload, timeout=60)

        if not resp.ok:
            return jsonify({"error": resp.text}), resp.status_code

        ocr_data = resp.json()
        json_path = os.path.splitext(save_path)[0] + "_result.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(ocr_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Veryfi OCR 成功: {json_path}")

        # === Step 2: JSON → UBL XML ===
        result = json_to_ubl_invoice(ocr_data)
        xml_path = os.path.splitext(save_path)[0] + "_invoice.xml"

        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(result["xml"])

        print(f"✅ UBL XML 已生成: {xml_path}")

        # === Step 3: 返回结果 ===
        return jsonify({
            "message": "OCR and XML success",
            "filename": file.filename,
            "summary": result["summary"],
            "missing_fields": result["missing_fields"],
            "xml_preview": result["xml"][:8000],
        }), 200

    except Exception as e:
        print(f"❌ Exception: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/convert_to_xml", methods=["POST"])
def convert_to_xml():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # 🔍 如果是 summary 格式，就补齐基本结构再传给转换函数
        if all(k in data for k in ["invoice_id", "issue_date", "due_date", "supplier_name", "customer_name", "total_amount"]):
            wrapped_data = {
                "invoice_number": data["invoice_id"],
                "date": data["issue_date"],
                "due_date": data["due_date"],
                "vendor": {"name": data["supplier_name"]},
                "bill_to": {"name": data["customer_name"], "address": "Unknown"},
                "total": float(data["total_amount"]),
                "currency_code": "AUD"
            }
        else:
            wrapped_data = data

        result = json_to_ubl_invoice(wrapped_data)

        return jsonify({
            "xml_preview": result["xml"][:8000],
            "summary": result["summary"],
            "missing_fields": result["missing_fields"],
        }), 200

    except Exception as e:
        print(f"❌ Exception in /api/convert_to_xml: {e}")
        return jsonify({"error": str(e)}), 500
        

@app.route("/api/update_xml", methods=["POST"])
def update_xml():
    """
    接收用户修改后的字段 -> 重新生成 XML
    """
    try:
        new_data = request.get_json()
        if not new_data:
            return jsonify({"error": "No data provided"}), 400

        result = json_to_ubl_invoice(new_data)
        xml_path = os.path.join(UPLOAD_FOLDER, "updated_invoice.xml")
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(result["xml"])

        return jsonify({
            "message": "XML updated successfully",
            "xml_preview": result["xml"][:8000],
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
