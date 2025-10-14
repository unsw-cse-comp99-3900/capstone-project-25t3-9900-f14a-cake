import os, uuid, datetime, json, io, sqlite3, bcrypt, jwt
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from functools import wraps

# ---------- Auth helpers (SQLite + bcrypt + JWT) ----------
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
            return jsonify({"error":"unauthorized"}), 401
        token = auth.split(" ",1)[1]
        try:
            payload = jwt.decode(token, jwt_secret(), algorithms=["HS256"])
            request.user_id = payload.get("sub")
        except Exception:
            return jsonify({"error":"invalid_token"}), 401
        return f(*args, **kwargs)
    return wrap

# ---------- File storage helpers ----------
def ensure_dirs(base: str):
    """Create three simple buckets: creation / validation / sending"""
    os.makedirs(base, exist_ok=True)
    for sub in ["creation", "validation", "sending"]:
        os.makedirs(os.path.join(base, sub), exist_ok=True)

def _store_one(file_storage, base_dir, section: str):
    """Save a single uploaded file under uploads/<section>/UUID.ext"""
    original = secure_filename(file_storage.filename or "")
    if not original:
        return None
    _, ext = os.path.splitext(original)
    saved = f"{uuid.uuid4().hex}{ext or ''}"
    dest = os.path.join(base_dir, section, saved)
    file_storage.save(dest)
    return {
        "original": original,
        "saved": saved,
        "section": section,
        "download_path": f"/download/{section}/{saved}"
    }

# ---------- Flask app factory ----------
def create_app():
    app = Flask(__name__)

    # Storage root (mounted as a volume in docker-compose)
    base_dir = os.path.join(os.getcwd(), "uploads")
    ensure_dirs(base_dir)

    # Limit upload size; align with Nginx client_max_body_size
    max_mb = int(os.environ.get("MAX_UPLOAD_MB", "50"))
    app.config["MAX_CONTENT_LENGTH"] = max_mb * 1024 * 1024

    # Init user DB
    init_db()

    # Health
    @app.get("/healthz")
    def healthz():
        return "ok"

    # Static download route per section
    @app.get("/download/<section>/<path:filename>")
    def download(section, filename):
        section = (section or "").lower()
        if section not in ["creation", "validation", "sending"]:
            return jsonify({"error":"unknown section"}), 400
        safe = os.path.basename(filename)
        return send_from_directory(os.path.join(base_dir, section), safe, as_attachment=True)

    # ---------- Auth ----------
    @app.post("/api/auth/register")
    def api_register():
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        if not email or not password:
            return jsonify({"error":"email/password required"}), 400
        try:
            db_exec("INSERT INTO users(email, password_hash) VALUES (?,?)", (email, hash_pw(password)))
            return jsonify({"ok": True})
        except sqlite3.IntegrityError:
            return jsonify({"error":"email already exists"}), 400

    @app.post("/api/auth/login")
    def api_login():
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        row = db_query_one("SELECT id, password_hash FROM users WHERE email=?", (email,))
        if not row:
            return jsonify({"error":"invalid credentials"}), 401
        uid, pw_hash = row[0], row[1]
        if not check_pw(password, pw_hash):
            return jsonify({"error":"invalid credentials"}), 401
        token = issue_token(uid)
        return jsonify({"token": token})

    # ---------- Upload-only endpoints ----------
    @app.post("/api/create")
    @require_auth
    def api_create():
        files = request.files.getlist("files")
        if not files:
            return jsonify({"error":"no files provided"}), 400
        outputs = []
        for f in files:
            rec = _store_one(f, base_dir, "creation")
            if rec: outputs.append(rec)
        return jsonify({"uploads": outputs})

    @app.post("/api/validate")
    @require_auth
    def api_validate():
        files = request.files.getlist("files")
        if not files:
            return jsonify({"error":"no file provided"}), 400
        rec = _store_one(files[0], base_dir, "validation")
        if not rec:
            return jsonify({"error":"empty filename"}), 400
        return jsonify({"upload": rec})

    @app.post("/api/send")
    @require_auth
    def api_send():
        files = request.files.getlist("files")
        if not files:
            return jsonify({"error":"no file provided"}), 400
        rec = _store_one(files[0], base_dir, "sending")
        if not rec:
            return jsonify({"error":"empty filename"}), 400
        return jsonify({"upload": rec})

    return app

if __name__ == "__main__":
    # Dev mode (use waitress in Dockerfile for production)
    create_app().run(host="0.0.0.0", port=5000, debug=True)
