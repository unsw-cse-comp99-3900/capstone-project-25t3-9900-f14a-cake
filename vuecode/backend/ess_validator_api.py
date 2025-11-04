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
    "Authorization": "Bearer eyJraWQiOiJqUWhhc1B3MXlhODluWVV5VDFIWHNab2dJWEJmRXlZWEZPeCtxV01WZHVJPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI3ZDMwYmk4N2lwdGVnYnJmMmJwMzdwNDJnZyIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiZWF0XC9yZWFkIiwiYXV0aF90aW1lIjoxNzYxOTE2Njk1LCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtY2VudHJhbC0xLmFtYXpvbmF3cy5jb21cL2V1LWNlbnRyYWwtMV9xdkNTNFdSdnoiLCJleHAiOjE3NjE5MjAyOTUsImlhdCI6MTc2MTkxNjY5NSwidmVyc2lvbiI6MiwianRpIjoiODgyM2QxMzEtZGFiZi00ODExLTkzMzUtMTBhNGM0YWUxYmMwIiwiY2xpZW50X2lkIjoiN2QzMGJpODdpcHRlZ2JyZjJicDM3cDQyZ2cifQ.ItXEZUA2TdvdtcYbXLH4koeLh7r39MXHvVcWqjyFIPvWor2UJNw2mXrIXNDy4Tpr7n280SnbNcLpINILrp5Wgh5ngMi8-yYtSFwnOAc9BbIqdwtKS-XjdMtSpJa-BVZqQ-xK9S_FfKUNcmfCS-66gEFyV6lKGXtb-KNvG6C7duEkt88bgFgSQcgwpZqPWCRAhXAhqUqimoHplN13gBZy_Mup7SnlkX_ap89SJLCHjwIQmtNgj5FTPQgykY5248NXg02gUiAxYr1OsOkagAWeAQuYAQMbPFrf0JeyKgGTOaAUlRkMv1P7zMJQzvLCYg8-qG4Hghnx-RQbBs5d7FkuDw",
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