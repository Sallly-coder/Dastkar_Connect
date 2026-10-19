# S1: bcrypt, JWT, @login_required, @role_required
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt
from flask import Blueprint, g, jsonify, request

from db import get_db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
VALID_ROLES = {"BUYER", "LIAISON", "ARTISAN"}


# ---------- 1. Hashing ----------

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def check_password(plain: str, hashed: str) -> bool:
    pw = plain.encode()
    if len(pw) > 72:  # bcrypt's limit
        return False
    return bcrypt.checkpw(pw, hashed.encode())


# ---------- 2. Register and login ----------

@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role")

    if not name or not email or not password or not role:
        return jsonify(error="name, email, password and role are required"), 400
    if role not in VALID_ROLES:
        return jsonify(error="role must be BUYER, LIAISON or ARTISAN"), 400
    if len(password) < 8 or len(password.encode()) > 72:
        return jsonify(error="password must be 8 to 72 characters"), 400

    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?,?,?,?)",
            (name, email, hash_password(password), role),
        )
        conn.commit()
        user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        return jsonify(error="Email already registered"), 409
    finally:
        conn.close()

    return jsonify(id=user_id, name=name, email=email, role=role), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    conn = get_db()
    try:
        user = conn.execute(
            "SELECT id, password_hash, role FROM users WHERE email = ?", (email,)
        ).fetchone()
    finally:
        conn.close()

    if user is None or not check_password(password, user["password_hash"]):
        # Same message for both cases, so attackers can't tell which emails exist
        return jsonify(error="Invalid email or password"), 401

    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {"sub": str(user["id"]), "role": user["role"], "iat": now, "exp": now + timedelta(days=1)},
        os.environ["SECRET_KEY"],
        algorithm="HS256",
    )
    return jsonify(token=token)


# ---------- 3. Token check (any logged-in user) ----------

def verify_token(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify(error="Missing or malformed Authorization header"), 401
        try:
            payload = jwt.decode(header[7:], os.environ["SECRET_KEY"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify(error="Token expired"), 401
        except jwt.InvalidTokenError:
            return jsonify(error="Invalid token"), 401

        g.user = {"id": int(payload["sub"]), "role": payload["role"]}
        return f(*args, **kwargs)
    return wrapper


# ---------- 4. Role guard ----------

def require_role(*roles):
    def decorator(f):
        @wraps(f)
        @verify_token
        def wrapper(*args, **kwargs):
            if g.user["role"] not in roles:
                return jsonify(error="Forbidden: insufficient role"), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


# ---------- Temporary test routes (delete later) ----------

@auth_bp.get("/me")
@verify_token
def me():
    return jsonify(g.user)


@auth_bp.get("/liaison-only")
@require_role("LIAISON")
def liaison_only():
    return jsonify(message="Welcome, liaison", user=g.user)