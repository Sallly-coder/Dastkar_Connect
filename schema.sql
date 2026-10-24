PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  name          TEXT NOT NULL,
  email         TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role          TEXT NOT NULL CHECK (role IN ('BUYER','LIAISON','ARTISAN')),
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);



CREATE TABLE IF NOT EXISTS media (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id   INTEGER NOT NULL REFERENCES orders(id),
  url        TEXT NOT NULL,
  type       TEXT NOT NULL CHECK (type IN ('INSPIRATION','FINAL')),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS orders (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  buyer_id        INTEGER NOT NULL REFERENCES users(id),
  artisan_id      INTEGER REFERENCES users(id),
  original_spec   TEXT NOT NULL,
  translated_spec TEXT,
  status          TEXT NOT NULL DEFAULT 'DRAFT'
                  CHECK (status IN ('DRAFT','ASSIGNED','REVIEW','COMPLETED')),
  price           INTEGER,
  payment_status  TEXT NOT NULL DEFAULT 'UNPAID'
                  CHECK (payment_status IN ('UNPAID','PAID')),
  payment_ref     TEXT,
  paid_at         DATETIME,
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
