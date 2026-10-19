# so that my user can test logging into the accounts for testing
import bcrypt
from db import get_db

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

USERS = [
    ("Test Buyer",   "buyer@test.com",   "buyer123",   "BUYER"),
    ("Test Liaison", "liaison@test.com", "liaison123", "LIAISON"),
    ("Test Artisan", "artisan@test.com", "artisan123", "ARTISAN"),
]

def seed_db():
    conn = get_db()
    for name, email, pw, role in USERS:
        conn.execute(
            "INSERT OR IGNORE INTO users (name, email, password_hash, role) VALUES (?,?,?,?)",
            (name, email, hash_password(pw), role),
        )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    seed_db()
    print("Seeded 3 users.")