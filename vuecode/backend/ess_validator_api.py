import base64
import requests
import hashlib

# === API 地址 ===
url = "https://services.ebusiness-cloud.com/ess-schematron/v1/api/validate"

# === 查询参数（指定验证规则） ===
params = {
    "rules": ["AUNZ_PEPPOL_1_0_10"],   #AUNZ_UBL_1_0_10 另一个
}

# === 认证与请求头 ===
headers = {
    "Authorization": (
        "Bearer eyJraWQiOiJqUWhhc1B3MXlhODluWVV5VDFIWHNab2dJWEJmRXlZWEZPeCtxV01WZHVJPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI3ZDMwYmk4N2lwdGVnYnJmMmJwMzdwNDJnZyIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiZWF0XC9yZWFkIiwiYXV0aF90aW1lIjoxNzYyMjI5NjYwLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtY2VudHJhbC0xLmFtYXpvbmF3cy5jb21cL2V1LWNlbnRyYWwtMV9xdkNTNFdSdnoiLCJleHAiOjE3NjIyMzMyNjAsImlhdCI6MTc2MjIyOTY2MCwidmVyc2lvbiI6MiwianRpIjoiODgzMGI3OWYtN2YyYi00ZDk0LWJhYmItNmU5YzNkMGI4M2YxIiwiY2xpZW50X2lkIjoiN2QzMGJpODdpcHRlZ2JyZjJicDM3cDQyZ2cifQ.A45OwsHeNQaT2l8flsvW_E437ISbMg8O89yxK3DajdS_b0jt8oVbper3Dv-IR17W3LTWFe_iZquUgl2HOohMO-5n3bSArMZ-lmn3GolVgVPHBhPOKrDGb6jiFo_E-FI5a8SFahvRnGq8UQ_fVSMNGVzeQ7zEPkibMQ0oQ2fm8MMtHy1QgYSe_q61Km9LPLiUylhZC5tsQqWKOim6nk0ke6e68S8zJUCALL5pyKSWqhYwXsi6ffUjEQfR4ZGMAhM96PFcwTSMZN5FS_cW4FDk5SEJtw2_3kTulGs3wl7urL-S_sg4WuMXchG8qVZcY-jlXH9l212UgyoFc8IGuziidw"
    ),
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# === 读取文件并准备 Base64 编码与 MD5 校验 ===
with open("2tax信息可通过.xml", "rb") as f:
    file_bytes = f.read()

base64_content = base64.b64encode(file_bytes).decode("utf-8")
checksum_md5 = hashlib.md5(base64_content.encode("utf-8")).hexdigest()

# === 构建请求体 ===
payload = {
    "filename": "invoice.xml",
    "content": base64_content,
    "checksum": checksum_md5
}

# === 发送请求 ===
response = requests.post(url, headers=headers, params=params, json=payload)

# === 输出结果 ===
print("状态码:", response.status_code)
print("响应内容:", response.text)
