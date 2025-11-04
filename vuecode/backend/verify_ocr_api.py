import base64
import requests
import json
import os

# === Veryfi 凭证 ===   这个并不是我的信息，你可以改成我的信息
CLIENT_ID = 'vrfCNjphfjSRisIrsp7ghDD26kfow1CRtcXSyoj'
AUTHORIZATION = 'apikey yudeqian66:c9944f183108cac9e66c1241cd5e2740'
url = "https://api.veryfi.com/api/v8/partner/documents/"

# === 要识别的发票文件 ===
input_pdf = "3page.pdf"
output_json = os.path.splitext(input_pdf)[0] + "_result.json"

# === 把文件编码为 Base64 ===
with open(input_pdf, "rb") as f:
    encoded_file = base64.b64encode(f.read()).decode("utf-8")

payload = {
    "file_data": encoded_file,   # 用 file_data 字段传文件内容
    "categories": ["Invoices"],  # 可选分类
    "auto_delete": True          # 上传后自动清理
}

headers = {
    "Content-Type": "application/json",
    "Client-Id": CLIENT_ID,
    "Authorization": AUTHORIZATION,
}

# === 调用 Veryfi API ===
resp = requests.post(url, headers=headers, json=payload)

# === 保存结果 ===
if resp.ok:
    data = resp.json()
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ OCR 成功！结果已保存到: {output_json}")
else:
    print(f"❌ 识别失败 ({resp.status_code})")
    print(resp.text)
