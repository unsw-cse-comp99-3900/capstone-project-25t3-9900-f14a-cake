import base64
import requests
import hashlib

# API 地址
url = "https://services.ebusiness-cloud.com/ess-schematron/v1/api/validate"

# 查询参数
params = {
    "rules": ["AUNZ_PEPPOL_1_0_10"],
}

# 认证与语言头
headers = {
    "Authorization": "Bearer eyJraWQiOiJqUWhhc1B3MXlhODluWVV5VDFIWHNab2dJWEJmRXlZWEZPeCtxV01WZHVJPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI3ZDMwYmk4N2lwdGVnYnJmMmJwMzdwNDJnZyIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiZWF0XC9yZWFkIiwiYXV0aF90aW1lIjoxNzYxODk4MDg1LCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtY2VudHJhbC0xLmFtYXpvbmF3cy5jb21cL2V1LWNlbnRyYWwtMV9xdkNTNFdSdnoiLCJleHAiOjE3NjE5MDE2ODUsImlhdCI6MTc2MTg5ODA4NSwidmVyc2lvbiI6MiwianRpIjoiOWNmYTA0MmMtYWYyNC00MmZlLThkODctOWM3YzcxZjExYWJjIiwiY2xpZW50X2lkIjoiN2QzMGJpODdpcHRlZ2JyZjJicDM3cDQyZ2cifQ.BpPrrjE9QCanjyk0FIyJsaOM4kdLyrt7nnqtpywWOI-rRKOH7WKZTwedrjMCTqLFShNf4Lbkqc3rFfWqixVDpvFSgNztL-8se9VjLNwhgd8WsCwU-I0jaouzXaBw4BYyMnWZTCd9A-Nw3OWuhzz8adQFLz-s5NMH-YEXl5YjS_2KoIzLpndIK3edGDK6vHGNNz8zL8bda6DJq7VICVH00YzpI6xZh6Wm06ZCM3lgAZnXFnOnm_ADDsWZ6bS6TAz7yuRP4ZhmL2-yBiFduydQlfrfgbQvDL0Myqsnzhu_dlcS0owIiFSmEvT6rtu3rEQOp6CD-SGGVnCwpVDBRe1TQA",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# === 读取文件并准备 Base64 和 MD5 ===
with open("invoice.xml", "rb") as f:
    file_bytes = f.read()

base64_content = base64.b64encode(file_bytes).decode("utf-8")
checksum_md5 = hashlib.md5(base64_content.encode("utf-8")).hexdigest()

# === 组织请求体 ===
payload = {
    "filename": "invoice.xml",
    "content": base64_content,
    "checksum": checksum_md5
}

# === 发送请求 ===
response = requests.post(url, headers=headers, params=params, json=payload)

print("状态码:", response.status_code)
print("响应内容:", response.text)