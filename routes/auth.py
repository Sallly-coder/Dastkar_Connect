# S1: /login, /register, /logout
import sqlite3

from flask import Blueprint, g, jsonify, request

from db import get_db
from security import check_password, create_token, hash_password, require_role, verify_token

auth_bp = Blueprint("auth", __name__)
VALID_ROLES = {"BUYER", "LIAISON", "ARTISAN"}


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
        return jsonify(error="Invalid email or password"), 401

    return jsonify(token=create_token(user["id"], user["role"]), role=user["role"])


@auth_bp.post("/logout")
@verify_token
def logout():
    # JWTs are stateless, so the server has nothing to delete.
    # The client logs out by discarding its stored token.
    return jsonify(message="Logged out")


# --- Temporary test routes: delete once teammates' routes exist ---

@auth_bp.get("/me")
@verify_token
def me():
    return jsonify(g.user)


@auth_bp.get("/liaison-only")
@require_role("LIAISON")
def liaison_only():
    return jsonify(message="Welcome, liaison", user=g.user)
