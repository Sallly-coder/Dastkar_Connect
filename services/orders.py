from contextlib import closing

from db import get_db
from services.uploads import detect_ext, save_photo


class OrderError(Exception):
    """A message that is safe to show the user. pages.py flashes it in red."""


def wrong_state(conn, order_id, expected):
    """Called only after an UPDATE changed 0 rows: explain why."""
    row = conn.execute("SELECT status FROM orders WHERE id = ?", (order_id,)).fetchone()
    if row is None:
        return "Order not found"
    if row["status"] == expected:
        return "Not your order"  # state was right, so the owner was wrong
    return f"Order is {row['status']}, expected {expected}"


def create_order(buyer_id, spec, photo):
    spec = (spec or "").strip()
    if not spec:
        raise OrderError("Please describe what you want")

    ext = None
    if photo and photo.filename:
        ext = detect_ext(photo)
        if ext is None:
            raise OrderError("Only JPG or PNG images are allowed")

    with closing(get_db()) as conn:
        order_id = conn.execute(
            "INSERT INTO orders (buyer_id, original_spec) VALUES (?, ?)",  # status defaults to DRAFT
            (buyer_id, spec),
        ).lastrowid
        if ext:
            conn.execute(
                "INSERT INTO media (order_id, url, type) VALUES (?, ?, 'INSPIRATION')",
                (order_id, save_photo(photo, ext)),
            )
        conn.commit()  # order + photo row saved together, or not at all
    return order_id


def assign_order(order_id, artisan_id, translated_spec, price):
    spec = (translated_spec or "").strip()
    if not spec:
        raise OrderError("Translation is required")
    try:
        price = int(price)
    except (TypeError, ValueError):
        raise OrderError("Enter the price in whole rupees")
    if price <= 0:
        raise OrderError("Price must be more than 0")

    with closing(get_db()) as conn:
        if not conn.execute(
            "SELECT 1 FROM users WHERE id = ? AND role = 'ARTISAN'", (artisan_id,)
        ).fetchone():
            raise OrderError("Invalid artisan")

        cur = conn.execute(
            """UPDATE orders
               SET artisan_id = ?, translated_spec = ?, price = ?, status = 'ASSIGNED',
                   payment_status = 'UNPAID', updated_at = CURRENT_TIMESTAMP
               WHERE id = ? AND status = 'DRAFT'""",
            (artisan_id, spec, price, order_id),
        )
        if cur.rowcount == 0:
            raise OrderError(wrong_state(conn, order_id, "DRAFT"))
        conn.commit()


def submit_payment_ref(buyer_id, order_id, ref):
    """Buyer (optional) types the UPI transaction ID so the liaison can match the payment."""
    ref = (ref or "").strip()
    if not ref:
        raise OrderError("Enter the UPI transaction ID")
    if len(ref) > 60:
        raise OrderError("Transaction ID is too long")
    with closing(get_db()) as conn:
        cur = conn.execute(
            """UPDATE orders SET payment_ref = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ? AND buyer_id = ? AND status = 'ASSIGNED' AND payment_status = 'UNPAID'""",
            (ref, order_id, buyer_id),
        )
        if cur.rowcount == 0:
            raise OrderError("This order is not waiting for payment")
        conn.commit()


def confirm_payment(order_id):
    """Liaison confirms the money reached the NGO account. Unlocks the order for the artisan."""
    with closing(get_db()) as conn:
        cur = conn.execute(
            """UPDATE orders
               SET payment_status = 'PAID', paid_at = CURRENT_TIMESTAMP,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = ? AND status = 'ASSIGNED' AND payment_status = 'UNPAID'""",
            (order_id,),
        )
        if cur.rowcount == 0:
            raise OrderError("This order is not waiting for payment")
        conn.commit()


def upload_final(artisan_id, order_id, photo):
    if not photo or not photo.filename:
        raise OrderError("Please take or choose a photo")
    ext = detect_ext(photo)
    if ext is None:
        raise OrderError("Only JPG or PNG images are allowed")

    with closing(get_db()) as conn:
        cur = conn.execute(
            """UPDATE orders
               SET status = 'REVIEW', updated_at = CURRENT_TIMESTAMP
               WHERE id = ? AND artisan_id = ? AND status = 'ASSIGNED'
                 AND payment_status = 'PAID'""",
            (order_id, artisan_id),
        )
        if cur.rowcount == 0:
            row = conn.execute(
                "SELECT status, artisan_id, payment_status FROM orders WHERE id = ?", (order_id,)
            ).fetchone()
            if (row and row["status"] == "ASSIGNED" and row["artisan_id"] == artisan_id
                    and row["payment_status"] != "PAID"):
                raise OrderError("Payment has not been confirmed yet")
            raise OrderError(wrong_state(conn, order_id, "ASSIGNED"))
        conn.execute(
            "INSERT INTO media (order_id, url, type) VALUES (?, ?, 'FINAL')",
            (order_id, save_photo(photo, ext)),
        )
        conn.commit()  # status change + photo row saved together


def approve_order(order_id):
    with closing(get_db()) as conn:
        cur = conn.execute(
            """UPDATE orders
               SET status = 'COMPLETED', updated_at = CURRENT_TIMESTAMP
               WHERE id = ? AND status = 'REVIEW'""",
            (order_id,),
        )
        if cur.rowcount == 0:
            raise OrderError(wrong_state(conn, order_id, "REVIEW"))
        conn.commit()


_LIST_BASE = """
    SELECT o.*,
      (SELECT url FROM media WHERE order_id = o.id AND type = 'INSPIRATION'
       ORDER BY id DESC LIMIT 1) AS inspiration_url,
      (SELECT url FROM media WHERE order_id = o.id AND type = 'FINAL'
       ORDER BY id DESC LIMIT 1) AS final_url
    FROM orders o
"""


def list_orders(user):
    """user is g.user: {"id": ..., "role": ...}"""
    if user["role"] == "BUYER":
        where, args = " WHERE o.buyer_id = ?", (user["id"],)
    elif user["role"] == "ARTISAN":
        where, args = " WHERE o.artisan_id = ? AND o.payment_status = 'PAID'", (user["id"],)
    else:  # LIAISON sees everything
        where, args = "", ()

    with closing(get_db()) as conn:
        rows = conn.execute(_LIST_BASE + where + " ORDER BY o.id DESC", args).fetchall()
    return [dict(r) for r in rows]


def list_artisans():
    with closing(get_db()) as conn:
        rows = conn.execute("SELECT id, name FROM users WHERE role = 'ARTISAN'").fetchall()
    return [dict(r) for r in rows]