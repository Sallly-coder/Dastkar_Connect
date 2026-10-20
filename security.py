
import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt
from flask import abort, flash, g, jsonify, redirect, request, url_for


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def check_password(plain: str, hashed: str) -> bool:
    pw = plain.encode()
    if len(pw) > 72:  # bcrypt's limit
        return False
    return bcrypt.checkpw(pw, hashed.encode())


def create_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user_id), "role": role, "iat": now, "exp": now + timedelta(days=1)},
        os.environ["SECRET_KEY"],
        algorithm="HS256",
    )


def _fail(message, api):
    if api:
        return jsonify(error=message), 401
    flash(message, "error")
    return redirect(url_for("auth.login"))


def verify_token(f):
    """Accepts the token from a Bearer header (API clients) or the 'token'
    cookie (browser pages). Sets g.user = {'id': ..., 'role': ...}."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        api = bool(header)
        token = header[7:] if header.startswith("Bearer ") else request.cookies.get("token")

        if not token:
            return _fail("Please log in", api)
        try:
            payload = jwt.decode(token, os.environ["SECRET_KEY"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return _fail("Session expired, please log in again", api)
        except jwt.InvalidTokenError:
            return _fail("Invalid session, please log in again", api)

        g.user = {"id": int(payload["sub"]), "role": payload["role"]}
        return f(*args, **kwargs)
    return wrapper


def require_role(*roles):
    def decorator(f):
        @wraps(f)
        @verify_token
        def wrapper(*args, **kwargs):
            if g.user["role"] not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator

login_required = verify_token
role_required = require_role
