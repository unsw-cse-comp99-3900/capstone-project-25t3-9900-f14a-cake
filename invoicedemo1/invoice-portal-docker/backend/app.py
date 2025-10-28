# backend/app.py
import os
import uuid
import json
import datetime
import sqlite3
import bcrypt
import jwt

from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from functools import wraps

# =========================
# Auth (SQLite + bcrypt + JWT)
# =========================

def db_path():
    return os.path.join(os.getcwd(), "auth", "users.db")

def db_exec(sql, params=()):
    con = sqlite3.connect(db_path())
    try:
        cur = con.cursor()
        cur.execute(sql, params)
        con.commit()
        return cur
    finally:
        con.close()

def db_query_one(sql, params=()):
    con = sqlite3.connect(db_path())
    try:
        cur = con.cursor()
        cur.execute(sql, params)
        return cur.fetchone()
    finally:
        con.close()

def init_db():
    os.makedirs(os.path.join(os.getcwd(), "auth"), exist_ok=True)
    db_exec("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash BLOB NOT NULL
    )
    """)

def hash_pw(pw: str) -> bytes:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt())

def check_pw(pw: str, hashed: bytes) -> bool:
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), hashed)
    except Exception:
        return False

def jwt_secret():
    return os.getenv("JWT_SECRET", "dev")

def jwt_ttl_min():
    return int(os.getenv("ACCESS_TOKEN_TTL_MIN", "60"))

def issue_token(user_id: int) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + datetime.timedelta(minutes=jwt_ttl_min())).timestamp()),
    }
    return jwt.encode(payload, jwt_secret(), algorithm="HS256")

def require_auth(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "unauthorized"}), 401
        token = auth.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, jwt_secret(), algorithms=["HS256"])
            request.user_id = payload.get("sub")
        except Exception:
            return jsonify({"error": "invalid_token"}), 401
        return f(*args, **kwargs)
    return wrap


# =========================
# File storage helpers
# =========================

SECTIONS = ["creation", "validation", "sending"]

def ensure_dirs(base: str):
    """Create three buckets: creation / validation / sending."""
    os.makedirs(base, exist_ok=True)
    for sub in SECTIONS:
        os.makedirs(os.path.join(base, sub), exist_ok=True)

def _store_one(file_storage, base_dir, section: str):
    """
    Save a single uploaded file under uploads/<section>/<uuid>.<ext>
    and write a meta JSON with the original name, so download uses original name.
    """
    original = secure_filename(file_storage.filename or "")
    if not original:
        return None

    _, ext = os.path.splitext(original)
    saved = f"{uuid.uuid4().hex}{ext or ''}"
    dest = os.path.join(base_dir, section, saved)
    file_storage.save(dest)

    # write meta with original filename
    meta_path = dest + ".meta.json"
    try:
        with open(meta_path, "w", encoding="utf-8") as mf:
            json.dump({"original": original}, mf, ensure_ascii=False)
    except Exception:
        pass  # non-fatal

    return {
        "original": original,
        "saved": saved,
        "section": section,
        "download_path": f"/download/{section}/{saved}"
    }


# =========================
# Flask app
# =========================

def create_app():
    app = Flask(__name__)

    # Storage root (mounted via docker-compose volume)
    base_dir = os.path.join(os.getcwd(), "uploads")
    ensure_dirs(base_dir)

    # Upload size limit (align with Nginx client_max_body_size)
    max_mb = int(os.environ.get("MAX_UPLOAD_MB", "50"))
    app.config["MAX_CONTENT_LENGTH"] = max_mb * 1024 * 1024

    # Init user DB
    init_db()

    # --- health ---
    @app.get("/healthz")
    def healthz():
        return "ok"

    # --- download: return original filename if present in meta ---
    @app.get("/download/<section>/<path:filename>")
    def download(section, filename):
        section = (section or "").lower()
        if section not in SECTIONS:
            return jsonify({"error": "unknown section"}), 400

        safe = os.path.basename(filename)
        folder = os.path.join(base_dir, section)
        file_path = os.path.join(folder, safe)

        # default to saved name; try read original from meta
        download_name = safe
        meta_path = file_path + ".meta.json"
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as mf:
                    meta = json.load(mf)
                    if isinstance(meta, dict) and meta.get("original"):
                        download_name = meta["original"]
            except Exception:
                pass

        return send_from_directory(
            folder,
            safe,
            as_attachment=True,
            download_name=download_name
        )

    # --- auth endpoints ---
    @app.post("/api/auth/register")
    def api_register():
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        if not email or not password:
            return jsonify({"error": "email/password required"}), 400
        try:
            db_exec("INSERT INTO users(email, password_hash) VALUES (?,?)", (email, hash_pw(password)))
            return jsonify({"ok": True})
        except sqlite3.IntegrityError:
            return jsonify({"error": "email already exists"}), 400

    @app.post("/api/auth/login")
    def api_login():
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        row = db_query_one("SELECT id, password_hash FROM users WHERE email=?", (email,))
        if not row:
            return jsonify({"error": "invalid credentials"}), 401
        uid, pw_hash = row[0], row[1]
        if not check_pw(password, pw_hash):
            return jsonify({"error": "invalid credentials"}), 401
        token = issue_token(uid)
        return jsonify({"token": token})

    # --- upload-only endpoints ---
    @app.post("/api/create")
    @require_auth
    def api_create():
        files = request.files.getlist("files")
        if not files:
            return jsonify({"error": "no files provided"}), 400
        outputs = []
        for f in files:
            rec = _store_one(f, base_dir, "creation")
            if rec:
                outputs.append(rec)
        return jsonify({"uploads": outputs})

    @app.post("/api/validate")
    @require_auth
    def api_validate():
        files = request.files.getlist("files")
        if not files:
            return jsonify({"error": "no file provided"}), 400
        rec = _store_one(files[0], base_dir, "validation")
        if not rec:
            return jsonify({"error": "empty filename"}), 400
        return jsonify({"upload": rec})

    @app.post("/api/send")
    @require_auth
    def api_send():
        files = request.files.getlist("files")
        if not files:
            return jsonify({"error": "no file provided"}), 400
        rec = _store_one(files[0], base_dir, "sending")
        if not rec:
            return jsonify({"error": "empty filename"}), 400
        return jsonify({"upload": rec})

    # --- NEW: UBL 2.1 XML from form (A-NZ friendly minimal set) ---
    @app.post("/api/creation/generate-ubl")
    @require_auth
    def api_creation_generate_ubl():
        """
        Request JSON:
        {
          "invoice_id": "INV-0001",
          "issue_date": "2025-10-16",
          "currency": "AUD",
          "customization_id": "",   # fill with A-NZ string when confirmed
          "profile_id": "",         # fill with A-NZ string when confirmed
          "supplier_name": "Supplier Ltd",
          "customer_name": "Customer Pty",
          "lines": [
            {"description":"Item A", "quantity": 2, "price": 45.50, "tax_rate": 0}
          ]
        }
        """
        data = request.get_json(silent=True) or {}

        inv_id   = (data.get("invoice_id") or "").strip() or f"INV-{uuid.uuid4().hex[:8]}"
        issue_dt = (data.get("issue_date") or "").strip() or datetime.date.today().isoformat()
        currency = (data.get("currency") or "AUD").strip().upper()
        customization_id = (data.get("customization_id") or "").strip()
        profile_id       = (data.get("profile_id") or "").strip()
        supplier = (data.get("supplier_name") or "Supplier Ltd").strip()
        customer = (data.get("customer_name") or "Customer Pty").strip()

        # lines: minimal support (>=1)
        lines = data.get("lines") or []
        if not isinstance(lines, list) or len(lines) == 0:
            return jsonify({"error": "lines must be a non-empty array"}), 400

        # accumulate totals
        line_items = []
        line_extension_total = 0.0
        tax_total_amount = 0.0

        for i, ln in enumerate(lines, start=1):
            desc = str(ln.get("description") or f"Item {i}")
            try:
                qty = float(ln.get("quantity") or 1)
                price = float(ln.get("price") or 0.0)
                tax_rate = float(ln.get("tax_rate") or 0.0)  # 0~1 or 0~100? assume 0~1 if <=1 else /100
                if tax_rate > 1.0:
                    tax_rate = tax_rate / 100.0
            except Exception:
                return jsonify({"error":"invalid line numbers"}), 400

            line_ext = round(qty * price, 2)
            tax_amt  = round(line_ext * tax_rate, 2)
            line_extension_total += line_ext
            tax_total_amount += tax_amt

            line_items.append({
                "id": i,
                "desc": desc,
                "qty": qty,
                "price": price,
                "line_amount": line_ext
            })

        tax_exclusive = round(line_extension_total, 2)
        tax_inclusive = round(tax_exclusive + tax_total_amount, 2)
        payable = tax_inclusive

        # Build minimal UBL 2.1 XML with required heads
        # Namespaces
        xml_lines = []
        for it in line_items:
            xml_lines.append(f"""
  <cac:InvoiceLine>
    <cbc:ID>{it['id']}</cbc:ID>
    <cbc:InvoicedQuantity unitCode="EA">{it['qty']:.4g}</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="{currency}">{it['line_amount']:.2f}</cbc:LineExtensionAmount>
    <cac:Item><cbc:Description>{it['desc']}</cbc:Description></cac:Item>
    <cac:Price><cbc:PriceAmount currencyID="{currency}">{it['price']:.2f}</cbc:PriceAmount></cac:Price>
  </cac:InvoiceLine>""")

        # Optional TaxTotal if there is tax
        tax_total_block = ""
        if tax_total_amount > 0:
            tax_total_block = f"""
  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="{currency}">{tax_total_amount:.2f}</cbc:TaxAmount>
  </cac:TaxTotal>"""

        head_custom_profile = ""
        if customization_id:
            head_custom_profile += f"\n  <cbc:CustomizationID>{customization_id}</cbc:CustomizationID>"
        if profile_id:
            head_custom_profile += f"\n  <cbc:ProfileID>{profile_id}</cbc:ProfileID>"

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:UBLVersionID>2.1</cbc:UBLVersionID>{head_custom_profile}
  <cbc:ID>{inv_id}</cbc:ID>
  <cbc:IssueDate>{issue_dt}</cbc:IssueDate>
  <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>{currency}</cbc:DocumentCurrencyCode>

  <cac:AccountingSupplierParty>
    <cac:Party><cac:PartyName><cbc:Name>{supplier}</cbc:Name></cac:PartyName></cac:Party>
  </cac:AccountingSupplierParty>

  <cac:AccountingCustomerParty>
    <cac:Party><cac:PartyName><cbc:Name>{customer}</cbc:Name></cac:PartyName></cac:Party>
  </cac:AccountingCustomerParty>

  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="{currency}">{line_extension_total:.2f}</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="{currency}">{tax_exclusive:.2f}</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="{currency}">{tax_inclusive:.2f}</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="{currency}">{payable:.2f}</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>{tax_total_block}
{''.join(xml_lines)}
</Invoice>
""".encode("utf-8")

        out_name = f"{inv_id}.xml"
        safe_out = secure_filename(out_name)
        out_path = os.path.join(base_dir, "creation", safe_out)
        with open(out_path, "wb") as wf:
            wf.write(xml)

        # Ensure download uses friendly original name
        try:
            with open(out_path + ".meta.json", "w", encoding="utf-8") as mf:
                json.dump({"original": safe_out}, mf, ensure_ascii=False)
        except Exception:
            pass

        return jsonify({"xml_download": f"/download/creation/{safe_out}"}), 200

    return app


if __name__ == "__main__":
    # Dev server (Dockerfile uses waitress in production)
    create_app().run(host="0.0.0.0", port=5000, debug=True)
