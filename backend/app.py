import os
import hmac
import hashlib
import json
from datetime import datetime, timezone

from flask import Flask, request, jsonify, make_response, redirect, render_template
import redis
from rq import Queue
from tou_api import tou_bp

app = Flask(__name__)
app.register_blueprint(tou_bp)

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
r = redis.from_url(REDIS_URL)
q = Queue("events", connection=r)

MAILGUN_SIGNING_KEY = os.environ.get("MAILGUN_SIGNING_KEY")
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*")
JWT_SECRET = os.environ.get("JWT_SECRET", os.urandom(32))
COOKIE_DOMAIN = os.environ.get("COOKIE_DOMAIN")  # e.g., .example.com for cross-subdomain
SESSION_TTL_MIN = int(os.environ.get("SESSION_TTL_MIN", "4320"))  # 3 days default
MAGIC_TTL_MIN = int(os.environ.get("MAGIC_TTL_MIN", "15"))
OTP_TTL_MIN = int(os.environ.get("OTP_TTL_MIN", "10"))
OTP_ATTEMPT_MAX = int(os.environ.get("OTP_ATTEMPT_MAX", "5"))


def cors(resp):
    origin = request.headers.get("Origin", "*")
    resp.headers["Access-Control-Allow-Origin"] = origin if ALLOWED_ORIGINS == "*" or origin in ALLOWED_ORIGINS.split(",") else "null"
    resp.headers["Vary"] = "Origin"
    resp.headers["Access-Control-Allow-Credentials"] = "true"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return resp


@app.route("/api/auth/start", methods=["POST"]) 
def auth_start():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    host = (data.get("host") or "").strip().lower()
    first_name = data.get("first_name")
    if not email:
        return cors((jsonify({"ok": False, "error": "email required"}), 400))
    if not is_registered(email):
        # Do not reveal registration status; respond success
        return cors(jsonify({"ok": True}))
    # Generate and store OTP
    code = issue_otp(email=email, ttl_min=OTP_TTL_MIN)
    try:
        from email_mailgun import send_mailgun
        send_mailgun("otp_code", to=email, variables={"first_name": first_name, "code": code, "minutes": OTP_TTL_MIN, "host": host})
    except Exception:
        pass
    return cors(jsonify({"ok": True}))


@app.route("/api/auth/verify", methods=["POST"]) 
def auth_verify():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    host = (data.get("host") or "").strip().lower()
    code = (data.get("code") or "").strip()
    if not (email and code):
        return cors((jsonify({"ok": False, "error": "email and code required"}), 400))
    ok, msg = verify_otp(email, code)
    if not ok:
        return cors((jsonify({"ok": False, "error": msg}), 401))
    # Issue session cookie (JWT)
    session_jwt = issue_session(email=email, host=host)
    resp = make_response(jsonify({"ok": True}))
    resp.set_cookie(
        "session",
        session_jwt,
        max_age=SESSION_TTL_MIN * 60,
        secure=True,
        httponly=True,
        samesite="Lax",
        domain=COOKIE_DOMAIN if COOKIE_DOMAIN else None,
    )
    return cors(resp)


@app.route("/api/auth/callback", methods=["GET"]) 
def auth_callback():
    token = request.args.get("token", "")
    payload = consume_magic_token(token)
    if not payload:
        return ("Invalid or expired link", 401)
    # Issue session cookie (JWT)
    session_jwt = issue_session(email=payload["email"], host=payload.get("host"))
    resp = make_response(redirect(payload.get("redirect", f"https://{payload.get('host') or ''}")))
    resp.set_cookie(
        "session",
        session_jwt,
        max_age=SESSION_TTL_MIN * 60,
        secure=True,
        httponly=True,
        samesite="Lax",
        domain=COOKIE_DOMAIN if COOKIE_DOMAIN else None,
    )
    return resp


@app.route("/api/auth/logout", methods=["POST"]) 
def auth_logout():
    # Client should include cookie; we add jti to a revocation set
    jwt_token = request.cookies.get("session")
    if jwt_token:
        revoke_session(jwt_token)
    resp = jsonify({"ok": True})
    resp = make_response(resp)
    resp.set_cookie("session", "", max_age=0)
    return cors(resp)


@app.route("/auth/login", methods=["GET"]) 
def auth_login_page():
    target = request.args.get("target") or f"https://{request.host}".replace(f"events.", "book.")
    return render_template("login.html", target=target)


@app.route("/auth/otp", methods=["GET"]) 
def auth_otp_page():
    email = request.args.get("email", "")
    target = request.args.get("target", "")
    return render_template("otp.html", email=email, target=target)


@app.route("/api/authz", methods=["GET"]) 
def authz():
    # For Traefik forwardAuth. Returns 200 if authorized, else 401.
    host = (request.headers.get("X-Forwarded-Host") or request.host).lower()
    jwt_token = request.cookies.get("session")
    if not jwt_token:
        return ("unauthorized", 401)
    valid, email = verify_session(jwt_token, host)
    if not valid or not email:
        return ("unauthorized", 401)
    # Enforce entitlement for this host
    try:
        if not has_user_entitlement(email, host):
            return ("forbidden", 403)
    except Exception:
        return ("unauthorized", 401)
    return ("ok", 200)


@app.route("/api/track", methods=["OPTIONS", "POST"])
def track():
    if request.method == "OPTIONS":
        return cors(app.make_default_options_response())
    try:
        event = request.get_json(force=True)
        event["received_at"] = datetime.now(timezone.utc).isoformat()
        q.enqueue("worker.handle_event", event)
        return cors(jsonify({"ok": True}))
    except Exception as e:
        return cors((jsonify({"ok": False, "error": str(e)}), 400))


@app.route("/api/email/mailgun/webhook", methods=["POST"]) 
def mailgun_webhook():
    # Verify signature per Mailgun docs
    if not MAILGUN_SIGNING_KEY:
        return ("signing key missing", 400)
    token = request.form.get("token", "")
    timestamp = request.form.get("timestamp", "")
    signature = request.form.get("signature", "")
    data = bytes(f"{timestamp}{token}", "utf-8")
    expected = hmac.new(MAILGUN_SIGNING_KEY.encode(), msg=data, digestmod=hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return ("invalid signature", 403)

    event = request.form.get("event-data") or json.dumps({
        "event": request.form.get("event"),
        "recipient": request.form.get("recipient"),
        "reason": request.form.get("reason"),
    })
    q.enqueue("worker.handle_mailgun_event", event)
    return ("ok", 200)


@app.route("/healthz")
def healthz():
    return {"ok": True}


# --- Helpers: registration & tokens ---
import base64, jwt, uuid
from db import user_active_licenses, has_user_entitlement

REGISTERED_SET = "registered_emails"  # legacy (Redis) — replaced by DB lookup
MAGIC_PREFIX = "magic:"
REVOKE_SET = "revoked:jti"


def is_registered(email: str) -> bool:
    # A user is "registered" if they have at least one active license
    try:
        lic = user_active_licenses(email)
        return len(lic) > 0
    except Exception:
        return False


def build_magic_link(token: str) -> str:
    base = os.environ.get("AUTH_BASE_URL") or f"https://{os.environ.get('EVENTS_DOMAIN','') }"
    return f"{base}/api/auth/callback?token={token}"


def issue_magic_token(email: str, host: str | None, ttl_min: int) -> str:
    payload = json.dumps({"email": email, "host": host, "iat": datetime.now(timezone.utc).timestamp()})
    token = base64.urlsafe_b64encode(os.urandom(24)).decode().rstrip("=")
    r.setex(MAGIC_PREFIX + token, ttl_min * 60, payload)
    return token


def consume_magic_token(token: str):
    key = MAGIC_PREFIX + token
    payload = r.get(key)
    if not payload:
        return None
    r.delete(key)
    try:
        return json.loads(payload)
    except Exception:
        return None


def issue_otp(email: str, ttl_min: int) -> str:
    # 6-digit numeric OTP, rate-limited by TTL
    code = f"{int.from_bytes(os.urandom(3), 'big') % 1000000:06d}"
    r.setex(f"otp:{email}", ttl_min * 60, code)
    r.setex(f"otp_attempts:{email}", ttl_min * 60, 0)
    return code


def verify_otp(email: str, code: str):
    key = f"otp:{email}"
    stored = r.get(key)
    if not stored:
        return False, "code expired"
    # Attempt counter
    akey = f"otp_attempts:{email}"
    try:
        attempts = int(r.get(akey) or 0)
    except Exception:
        attempts = 0
    if attempts >= OTP_ATTEMPT_MAX:
        return False, "too many attempts"
    if code != stored.decode():
        r.set(akey, attempts + 1)
        return False, "invalid code"
    # Success: consume code
    r.delete(key)
    r.delete(akey)
    return True, "ok"


def issue_session(email: str, host: str | None):
    jti = str(uuid.uuid4())
    exp = datetime.now(timezone.utc) + timedelta(minutes=SESSION_TTL_MIN)
    claims = {"sub": email, "jti": jti, "exp": int(exp.timestamp()), "host": host}
    return jwt.encode(claims, JWT_SECRET, algorithm="HS256")


def verify_session(token: str, host: str | None):
    try:
        claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if r.sismember(REVOKE_SET, claims.get("jti")):
            return False, None
        # Optional: host pinning
        pinned = claims.get("host")
        if pinned and host and pinned != host:
            return False, None
        return True, claims.get("sub")
    except Exception:
        return False, None


def revoke_session(token: str):
    try:
        claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], options={"verify_exp": False})
        jti = claims.get("jti")
        if jti:
            # Store with TTL equal to remaining lifetime
            exp_ts = claims.get("exp") or 0
            ttl = max(0, exp_ts - int(datetime.now(timezone.utc).timestamp()))
            r.sadd(REVOKE_SET, jti)
            if ttl > 0:
                r.expire(REVOKE_SET, ttl)
    except Exception:
        pass


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)
