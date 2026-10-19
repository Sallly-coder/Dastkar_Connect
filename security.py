
import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt
from flask import g, jsonify, request


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