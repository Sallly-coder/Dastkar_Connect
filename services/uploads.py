import os
import uuid

from flask import current_app


def detect_ext(file):
    """Check the file's real first bytes, not the name or type the browser claims.
    Returns ".jpg", ".png", or None if it is neither."""
    head = file.stream.read(8)
    file.stream.seek(0)  # rewind, or save() would start from the wrong place
    if head.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    return None


def save_photo(file, ext):
    """Save into uploads/ under a random name. Returns the path stored in media.url."""
    name = uuid.uuid4().hex + ext  # never use the user's own filename
    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], name))
    return f"/uploads/{name}"