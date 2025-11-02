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

        # === Step 2: 保存 JSON 文件 ===
        ocr_data = resp.json()
        json_path = os.path.splitext(save_path)[0] + "_result.json"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(ocr_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Veryfi OCR 成功: {json_path}")

        # === Step 3: 从 JSON 文件重新读取（保证一致性） ===
        with open(json_path, "r", encoding="utf-8") as f:
            json_loaded = json.load(f)

        print("🟢 JSON 重新载入成功，字段示例：")
        print({
            "invoice_number": json_loaded.get("invoice_number"),
            "date": json_loaded.get("date"),
            "subtotal": json_loaded.get("subtotal"),
            "total": json_loaded.get("total"),
            "vendor": json_loaded.get("vendor", {}).get("name"),
            "bill_to": json_loaded.get("bill_to", {}).get("name"),
        })

        # === Step 4: JSON → UBL XML ===
        result = json_to_ubl_invoice(json_loaded)

        xml_path = os.path.splitext(save_path)[0] + "_invoice.xml"
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(result["xml"])

        print(f"✅ UBL XML 已生成: {xml_path}")

        # === Step 5: 返回结果 ===
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

        def to_float(x, default=0.0):
            try:
                return float(x)
            except Exception:
                return default

        # === 情况 A：payload 是 { summary: {...}, ... } 的“外壳”格式（你这次就是这种）
        if isinstance(data.get("summary"), dict):
            s = data["summary"]
            print("🔍 Detected summary-wrapper JSON")

            invoice_no = s.get("invoice_number") or s.get("invoice_id")
            total_value = s.get("total") or s.get("total_amount")
            subtotal_value = s.get("subtotal", total_value)

            wrapped_data = {
                # json_to_ubl_invoice 期望的字段命名
                "invoice_number": invoice_no,
                "date": s.get("issue_date") or s.get("date"),     # ✅ 用 issue_date 填到 date，避免 fallback 到今天
                "due_date": s.get("due_date"),
                "currency_code": s.get("currency_code", "AUD"),
                "subtotal": to_float(subtotal_value, 0.0),
                "total": to_float(total_value, 0.0),
                "country_code": s.get("country_code", "AU"),
                "document_type": s.get("document_type", "Invoice"),
                "document_title": s.get("document_title", f"Invoice {invoice_no}"),
                "reference_number": s.get("reference_number", invoice_no),
                "created_date": s.get("created_date"),

                # 供应商 / 客户按期望的嵌套结构包装
                "vendor": {
                    "name": s.get("supplier_name") or "Unknown Supplier",
                    "address": s.get("supplier_address") or "Address Not Provided",
                    # 可选： "abn_number": s.get("supplier_abn")
                },
                "bill_to": {
                    "name": s.get("customer_name") or "Unknown Customer",
                    "address": s.get("customer_address") or "Address Not Provided",
                    # 可选： "vat_number": s.get("customer_abn")
                },

                # 若上层额外给了明细，就带过去；否则给空列表
                "line_items": data.get("line_items", []),
            }

        # === 情况 B：payload 是扁平的 summary（没有 summary 外壳）
        elif all(k in data for k in [
            "invoice_number", "issue_date", "due_date",
            "supplier_name", "customer_name", "total"
        ]) or all(k in data for k in [
            "invoice_id", "issue_date", "due_date",
            "supplier_name", "customer_name", "total_amount"
        ]):
            print("🔍 Detected flat-summary JSON")

            invoice_no = data.get("invoice_number") or data.get("invoice_id")
            total_value = data.get("total") or data.get("total_amount")
            subtotal_value = data.get("subtotal", total_value)

            wrapped_data = {
                "invoice_number": invoice_no,
                "date": data.get("issue_date") or data.get("date"),  # ✅ 关键点
                "due_date": data.get("due_date"),
                "currency_code": data.get("currency_code", "AUD"),
                "subtotal": to_float(subtotal_value, 0.0),
                "total": to_float(total_value, 0.0),
                "country_code": data.get("country_code", "AU"),
                "document_type": data.get("document_type", "Invoice"),
                "document_title": data.get("document_title", f"Invoice {invoice_no}"),
                "reference_number": data.get("reference_number", invoice_no),
                "vendor": {
                    "name": data.get("supplier_name") or "Unknown Supplier",
                    "address": data.get("supplier_address") or "Address Not Provided",
                },
                "bill_to": {
                    "name": data.get("customer_name") or "Unknown Customer",
                    "address": data.get("customer_address") or "Address Not Provided",
                },
                "line_items": data.get("line_items", []),
            }

        # === 情况 C：Veryfi 原始 JSON（含 vendor/bill_to/date 等）
        else:
            print("🔍 Detected raw Veryfi JSON")
            wrapped_data = data

        print("🧾 Wrapped data (before conversion):")
        print(json.dumps(wrapped_data, indent=2, ensure_ascii=False))

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
