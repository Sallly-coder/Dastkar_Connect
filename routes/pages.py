from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, g, current_app, send_from_directory)
from security import login_required, role_required
from services import orders
from services.orders import OrderError

bp = Blueprint("pages", __name__)
HOME = {"BUYER": "pages.buyer", "LIAISON": "pages.liaison", "ARTISAN": "pages.artisan"}


def attempt(action, ok_message):
    """Run a service call and flash success or the error message."""
    try:
        action()
        flash(ok_message, "ok")
    except OrderError as e:
        flash(str(e), "error")

@bp.get("/")
@login_required
def home():
    return redirect(url_for(HOME[g.user["role"]]))

# ---- Buyer ----
@bp.get("/buyer")
@role_required("BUYER")
def buyer():
    return render_template("buyer.html", orders=orders.list_orders(g.user))

@bp.post("/buyer/orders")
@role_required("BUYER")
def buyer_create():
    attempt(lambda: orders.create_order(
        g.user["id"], request.form.get("original_spec"), request.files.get("photo")),
        "Order submitted")
    return redirect(url_for("pages.buyer"))

# ---- Liaison ----
@bp.get("/liaison")
@role_required("LIAISON")
def liaison():
    return render_template("liaison.html",
                           orders=orders.list_orders(g.user), artisans=orders.list_artisans())

@bp.post("/liaison/assign/<int:order_id>")
@role_required("LIAISON")
def liaison_assign(order_id):
    attempt(lambda: orders.assign_order(
        order_id, request.form.get("artisan_id"), request.form.get("translated_spec")),
        "Order assigned")
    return redirect(url_for("pages.liaison"))

@bp.post("/liaison/approve/<int:order_id>")
@role_required("LIAISON")
def liaison_approve(order_id):
    attempt(lambda: orders.approve_order(order_id), "Order approved")
    return redirect(url_for("pages.liaison"))

# ---- Artisan ----
@bp.get("/artisan")
@role_required("ARTISAN")
def artisan():
    task = next((o for o in orders.list_orders(g.user) if o["status"] == "ASSIGNED"), None)
    return render_template("artisan.html", task=task)

@bp.post("/artisan/upload/<int:order_id>")
@role_required("ARTISAN")
def artisan_upload(order_id):
    attempt(lambda: orders.upload_final(g.user["id"], order_id, request.files.get("photo")),
            "Photo uploaded")
    return redirect(url_for("pages.artisan"))

# ---- Photos ----
@bp.get("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
