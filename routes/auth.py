import sqlite3

from flask import (Blueprint, flash, g, jsonify, redirect, render_template,
                   request, url_for, session)  # Added session here

from db import get_db
from security import check_password, create_token, hash_password, require_role, verify_token

auth_bp = Blueprint("auth", __name__)

# Where each role lands after login. Replace the endpoints once your
# teammates agree on their page names.
ROLE_HOME = {
    "BUYER": "pages.home",
    "LIAISON": "pages.home",
    "ARTISAN": "pages.home",
}


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        if not name or not email or not password:
            flash("Name, email and password are required", "error")
        elif len(password) < 8 or len(password.encode()) > 72:
            flash("Password must be 8 to 72 characters", "error")
        else:
            conn = get_db()
            try:
                conn.execute(
                    "INSERT INTO users (name, email, password_hash, role) VALUES (?,?,?,?)",
                    (name, email, hash_password(password), "BUYER"),  # role is forced
                )
                conn.commit()
            except sqlite3.IntegrityError:
                flash("Email already registered", "error")
            else:
                flash("Account created. Please log in.", "success")
                return redirect(url_for("auth.login"))
            finally:
                conn.close()
    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        conn = get_db()
        try:
            user = conn.execute(
                "SELECT id, password_hash, role FROM users WHERE email = ?", (email,)
            ).fetchone()
        finally:
            conn.close()

        if user is None or not check_password(password, user["password_hash"]):
            flash("Invalid email or password", "error")
        else:
            resp = redirect(url_for(ROLE_HOME[user["role"]]))
            resp.set_cookie(
                "token",
                create_token(user["id"], user["role"]),
                httponly=True,   # JavaScript can't read it
                samesite="Lax",
                max_age=86400,   # 1 day, same as the token
            )
            return resp
    return render_template("login.html")


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    # Clear the current session
    session.clear()

    # Clear the authentication cookie
    resp = redirect(url_for("pages.login"))
    resp.set_cookie("token", "", expires=0)

    return resp


# --- Temporary test routes: delete once teammates' routes exist ---

@auth_bp.get("/me")
@verify_token
def me():
    return jsonify(g.user)


@auth_bp.get("/liaison-only")
@require_role("LIAISON")
def liaison_only():
    return jsonify(message="Welcome, liaison", user=g.user)
