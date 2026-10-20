import os

from dotenv import load_dotenv
from flask import Flask

load_dotenv()

from init_db import init_db
from seed import seed_db
from routes.auth import auth_bp
from routes.pages import bp as pages_bp

if not os.environ.get("SECRET_KEY"):
    raise RuntimeError("SECRET_KEY is missing. Create a .env file.")

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

app.register_blueprint(auth_bp)
app.register_blueprint(pages_bp)


@app.cli.command("init-db")
def init_db_command():
    """Create the database tables."""
    init_db()


@app.cli.command("seed")
def seed_command():
    """Insert the test users."""
    seed_db()
    print("Seeded 3 users.")
