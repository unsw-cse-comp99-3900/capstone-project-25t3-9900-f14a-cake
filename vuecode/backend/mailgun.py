import requests
import os

# === 必改部分 ===
MAILGUN_DOMAIN = "sandbox6f879be050d64593af6ed0a5716d7fe7.mailgun.org"  # 你的 Mailgun 域名
MAILGUN_API_KEY = "2a4beb5574c7249774639fd46166081f-02300200-80d8610e"                  # 你的 Private API key
TO_EMAIL = "gaohang_max@outlook.com"                                # 收件人（记得在 Mailgun 后台 Authorized Recipients 里验证）
XML_FILE_PATH = r"C:\Users\Lenovo\Downloads\invoice-yd (1)\test.xml"             # 你的 XML 文件路径

# === 可改部分 ===
FROM_EMAIL = f"Mailgun Sandbox <postmaster@{MAILGUN_DOMAIN}>"
SUBJECT = "Mailgun XML Attachment Test"
TEXT_BODY = "Hello, this is a test email sent via Mailgun API with an XML attachment."


def send_xml_mail():
    if not os.path.exists(XML_FILE_PATH):
        print(f"[ERROR] XML file not found: {XML_FILE_PATH}")
        return

    with open(XML_FILE_PATH, "rb") as xml_file:
        files = [("attachment", (os.path.basename(XML_FILE_PATH), xml_file, "application/xml"))]
        data = {
            "from": FROM_EMAIL,
            "to": TO_EMAIL,
            "subject": SUBJECT,
            "text": TEXT_BODY,
        }

        print("[INFO] Sending request to Mailgun...")
        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            data=data,
            files=files,
        )

    print("[INFO] Status Code:", response.status_code)
    print("[INFO] Response:", response.text)


if __name__ == "__main__":
    send_xml_mail()
