# Dastkar Connect

**Artisan Custom Co-Creation Portal.** A web platform that connects urban buyers with rural artisans through an NGO liaison.

Rajasthan's artisans make blue pottery, block prints, lac bangles and embroidery, but three gaps stand between them and urban buyers: **language, digital access and trust**. Dastkar Connect closes those gaps with a three-sided workflow:

| Role | What they do on the platform |
| --- | --- |
| **Urban Buyer** | Describes a custom craft item, attaches a reference photo, pays the NGO by UPI QR, and receives the finished product's photo |
| **NGO Liaison** | Translates the request for the artisan, sets the price, assigns an artisan, confirms the buyer's payment, and approves the finished work |
| **Rural Artisan** | Sees the paid task in simple, large text and uploads a photo of the finished work from a phone camera |

The project was built as a one-week MVP by three students. The frontend is server-rendered and contains **no custom JavaScript**.

---

## Contents

1. [Features](#features)
2. [Tech stack](#tech-stack)
3. [Project structure](#project-structure)
4. [Getting started](#getting-started)
5. [Demo accounts](#demo-accounts)
6. [Order lifecycle and business rules](#order-lifecycle-and-business-rules)
7. [Pages and routes](#pages-and-routes)
8. [Data model](#data-model)
9. [Security](#security)
10. [Running the tests](#running-the-tests)
11. [Troubleshooting](#troubleshooting)
12. [Known limitations](#known-limitations)
13. [Team and roles](#team-and-roles)

---

## Features

**All users**
- Login and logout with a signed session cookie; each role is redirected to its own page
- Green and red flash messages for every success or error
- Mobile-friendly layout (phone first, wider layouts from 600 px up)

**Buyer** (`/buyer`)
- Craft showcase: 6 Rajasthani crafts with photo and description (display only)
- Order form: required description, optional JPG/PNG reference photo
- Order cards with status badges
- Payment box for assigned, unpaid orders: price, NGO name, UPI ID, NGO's QR code, and a field to save the UPI transaction ID
- Final photo shown once the order is completed

**Liaison** (`/liaison`)
- One card per order with the buyer's request, reference photo, translation, artisan and price
- Next action only: assign (translation, artisan, price), confirm payment, or approve finished work

**Artisan** (`/artisan`)
- Shows the first order that is assigned to them **and** paid
- Translated instructions in large text, the buyer's reference photo, and a camera-ready upload field (`capture="environment"` opens the rear camera on phones)

---

## Tech stack

| Layer | Technology |
| --- | --- |
| Language and framework | Python 3, Flask |
| Templates | Jinja2 (server-rendered HTML and plain forms, no custom JavaScript) |
| Database | SQLite (`database.db`) through Python's built-in `sqlite3`, raw SQL |
| Passwords | bcrypt (salted hashes) |
| Sessions | JWT (PyJWT) in an HttpOnly, SameSite=Lax cookie |
| Configuration | python-dotenv (`.env`) |
| Styling | Hand-written CSS with variables; fonts Plus Jakarta Sans and Playfair Display |
| Tests | Selenium WebDriver (Chrome) with pytest |

---

## Project structure

```
Dastkar_Connect/
├── app.py                  # Creates the Flask app, loads config, registers blueprints
├── db.py                   # SQLite connection (foreign keys on)
├── security.py             # bcrypt, JWT, @verify_token, @require_role
├── schema.sql              # Tables: users, orders, media
├── init_db.py              # Creates database.db from schema.sql
├── seed.py                 # Creates the 3 core demo accounts
├── create_user.py          # Adds one user from the command line
├── requirements.txt
├── .env.example            # Template for the .env file
├── .gitignore
├── README.md
├── routes/
│   ├── auth.py             # /login, /register, /logout
│   └── pages.py            # All page routes (buyer, liaison, artisan, uploads)
├── services/
│   ├── orders.py           # Order rules, status changes, payment steps, SQL
│   └── uploads.py          # Image check (JPG/PNG signature) and saving
├── templates/
│   ├── base.html           # Shared layout, header, flash messages
│   ├── login.html
│   ├── register.html
│   ├── buyer.html
│   ├── liaison.html
│   └── artisan.html
├── static/
│   ├── css/style.css
│   └── img/
│       ├── payment_qr.png  # The NGO's UPI QR code
│       └── crafts/         # 6 showcase photos
├── uploads/                # Uploaded order photos (created at runtime)
├── tests/
│   └── test_login_selenium.py
└── screenshots/            # Test evidence (generated, not committed)
```

**How a request flows:**

```
Browser → routes (auth.py / pages.py) → security.py (who are you, which role?)
        → services (business rules, SQL) → SQLite + uploads/
        ← Jinja2 template renders the HTML page
```

---

## Getting started

### 1. Requirements

- Python 3.10 or newer
- Google Chrome (only needed for the Selenium tests)

### 2. Install

**Windows (Command Prompt)**
```
cd Dastkar_Connect
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**macOS / Linux**
```
cd Dastkar_Connect
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Your prompt should start with `(venv)` once the environment is active.

### 3. Configure

Copy the template and edit it:

```
copy .env.example .env          # Windows
cp .env.example .env            # macOS / Linux
```

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Signs login tokens and flash messages. Use a long random value. |
| `SEED_PASSWORD` | Password given to the demo accounts (8 to 72 characters) |
| `UPI_ID` | The NGO's UPI ID, shown to buyers beside the QR code |
| `NGO_NAME` | The NGO's name, shown in the payment box |

Generate a secret key:

```
python -c "import secrets; print(secrets.token_hex(32))"
```

**Payment QR:** save the NGO's UPI QR image as `static/img/payment_qr.png`.

**Craft showcase photos:** `static/img/crafts/` must contain these 6 files (the names must match exactly): `blue-pottery.jpeg`, `block-printing.jpeg`, `lac-bangles.jpeg`, `gotta-patti.jpeg`, `split-ply-weaving.jpeg`, `danka-embroidery.jpg`. Use photos you have the right to use.

### 4. Create the database and demo users

```
python init_db.py
python seed.py
```

`init_db.py` uses `CREATE TABLE IF NOT EXISTS`, so it does not add columns to an existing table. After any change to `schema.sql`, delete `database.db` and run both commands again.

To add more accounts (including extra artisans so the Liaison has a choice):

```
python create_user.py "Ramesh Kumar - Pottery"  ramesh@example.com  YourPassword123 ARTISAN
python create_user.py "Shanti Bai - Embroidery" shanti@example.com  YourPassword123 ARTISAN
python create_user.py "Priya Nair"              priya@example.com   YourPassword123 BUYER
```

### 5. Run

```
flask --app app run --debug
```

Open **http://127.0.0.1:5000**. Stop the server with `Ctrl+C`.

**To test on a phone** (same Wi-Fi network):

```
flask --app app run --debug --host 0.0.0.0
```

Find the computer's IPv4 address with `ipconfig` (Windows) or `ifconfig` (macOS/Linux) and open `http://<that-address>:5000` on the phone.

---

## Demo accounts

Created by `seed.py`. The password for all of them is the value of `SEED_PASSWORD` in your `.env`.

| Role | Name | Email |
| --- | --- | --- |
| Liaison | Meera Joshi | `meera@example.com` |
| Artisan | Lakshmi Devi - Block Printing | `lakshmi@example.com` |
| Buyer | Aarav Mehta | `aarav@example.com` |

Public registration (`/register`) creates **buyer** accounts only. Liaison and artisan accounts are created with `seed.py` or `create_user.py`.

**Using three roles at once:** the login cookie is shared by every tab of one browser. Use a separate browser (or a private window) for each role.

---

## Order lifecycle and business rules

```
DRAFT ──assign──▶ ASSIGNED ──artisan uploads──▶ REVIEW ──approve──▶ COMPLETED
         (Liaison)    ▲                          (Artisan)            (Liaison)
                      │
            payment: UNPAID ──confirm──▶ PAID    (Liaison)
```

| Step | Who | What happens | Order status | Payment status |
| --- | --- | --- | --- | --- |
| 1 | Buyer | Submits description and optional photo | `DRAFT` | `UNPAID` |
| 2 | Liaison | Writes the translation, sets a whole-rupee price, picks an artisan | `ASSIGNED` | `UNPAID` |
| 3 | Buyer | Pays the NGO by UPI and may save the transaction ID | `ASSIGNED` | `UNPAID` |
| 4 | Liaison | Checks the UPI app and confirms the payment | `ASSIGNED` | `PAID` |
| 5 | Artisan | Sees the task and uploads a photo of the finished work | `REVIEW` | `PAID` |
| 6 | Liaison | Checks the photo and approves | `COMPLETED` | `PAID` |

**Rules**
- Each status change is a single SQL `UPDATE` that names the required current status in its `WHERE` clause. If no row changes, the order was in the wrong state and the user sees an error.
- The buyer pays the **NGO**, not the artisan. The NGO pays the artisan outside the system after approval.
- An artisan only sees, and can only upload to, orders that are assigned to them **and** paid.
- Buyers see only their own orders. Liaisons see all orders.
- Only the Liaison can assign, confirm payment and approve.

---

## Pages and routes

| Method | URL | Role | Purpose |
| --- | --- | --- | --- |
| GET, POST | `/login` | Anyone | Log in |
| GET, POST | `/register` | Anyone | Create a buyer account |
| GET, POST | `/logout` | Anyone | Delete the session cookie |
| GET | `/` | Logged in | Redirect to the page for the user's role |
| GET | `/buyer` | Buyer | Showcase, order form, order cards |
| POST | `/buyer/orders` | Buyer | Create an order |
| POST | `/buyer/pay-ref/<order_id>` | Buyer | Save the UPI transaction ID |
| GET | `/liaison` | Liaison | All orders and next actions |
| POST | `/liaison/assign/<order_id>` | Liaison | Save translation, price, artisan |
| POST | `/liaison/confirm-payment/<order_id>` | Liaison | Mark the order as paid |
| POST | `/liaison/approve/<order_id>` | Liaison | Approve finished work |
| GET | `/artisan` | Artisan | The current task |
| POST | `/artisan/upload/<order_id>` | Artisan | Upload the finished-work photo |
| GET | `/uploads/<file>` | Anyone with the link | Serve an uploaded image |

Every POST ends with a redirect to a GET page (Post/Redirect/Get), so refreshing never resubmits a form. HTML forms only support GET and POST, which is why updates use POST.

---

## Data model

SQLite, three tables, with `CHECK` constraints and foreign keys switched on.

**`users`**: `id`, `name`, `email` (unique), `password_hash`, `role` (`BUYER` / `LIAISON` / `ARTISAN`), `created_at`

**`orders`**: `id`, `buyer_id`, `artisan_id` (empty until assigned), `original_spec`, `translated_spec`, `status` (`DRAFT` / `ASSIGNED` / `REVIEW` / `COMPLETED`), `price` (whole rupees), `payment_status` (`UNPAID` / `PAID`), `payment_ref`, `paid_at`, `created_at`, `updated_at`

**`media`**: `id`, `order_id`, `url` (path under `/uploads`), `type` (`INSPIRATION` / `FINAL`), `created_at`

Relationships: a user (buyer) has many orders; a user (artisan) is assigned many orders; an order has many media rows.

---

## Security

| Concern | What the project does |
| --- | --- |
| Passwords | Stored only as salted bcrypt hashes; 8 to 72 characters |
| Sessions | Signed JWT with a one-day expiry, in an HttpOnly, SameSite=Lax cookie |
| Access control | `@verify_token` redirects to login; `@require_role` returns 403 for the wrong role |
| Login errors | One message for an unknown email and a wrong password |
| Self-registration | Always creates a buyer |
| SQL injection | Every query uses `?` placeholders |
| Cross-site scripting | Jinja2 escapes every `{{ }}` value |
| Uploads | Only JPG and PNG, checked by the file's first bytes; saved under a random name; 5 MB limit; only the path is stored in the database |
| Secrets | `.env` and `database.db` are excluded from version control |

---

## Running the tests

The Selenium tests drive a real Chrome browser against the running app. They only read from the database, so they do not change your data. They need the demo accounts from `seed.py`.

```
pip install selenium pytest
```

**Command Prompt 1:** start the app and leave it running

```
cd Dastkar_Connect
venv\Scripts\activate
flask --app app run
```

**Command Prompt 2:** run the tests

```
cd Dastkar_Connect
venv\Scripts\activate
python -m pytest tests\test_login_selenium.py -v
```

Set `HEADLESS=1` first to hide the browser window. Each test saves a screenshot to `screenshots/`.

| ID | Test case | Expected result |
| --- | --- | --- |
| TC01 | Log in with valid data | Logged in; session cookie set |
| TC02 | Log in as each of the 3 roles | Lands on `/buyer`, `/liaison` or `/artisan` |
| TC03 | Valid email, wrong password | Stays on login with an error; no cookie |
| TC04 | Unregistered email | Same error; no cookie |
| TC05 | Empty email | Not logged in |
| TC06 | Empty password | Not logged in |
| TC07 | Open `/buyer` without logging in | Redirected to `/login` |
| TC08 | Buyer opens `/liaison` | 403 Forbidden |
| TC09 | Log out, then open `/buyer` | Redirected to `/login` |
| TC10 | Tampered session cookie | Redirected to `/login` |

---

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `ModuleNotFoundError: No module named 'dotenv'` | The virtual environment is not active. Run `venv\Scripts\activate`, then `pip install -r requirements.txt`. |
| `KeyError: 'SECRET_KEY'` | `.env` is missing or has no `SECRET_KEY`. |
| `no such column` or `no such table` | `database.db` is older than `schema.sql`. Delete it and run `init_db.py` and `seed.py`. |
| Cannot delete `database.db` on Windows | The server is still running. Stop it with `Ctrl+C` first. |
| `TemplateNotFound` | A file in `templates/` is missing or misnamed. |
| Craft photos or QR show as empty boxes | The file names in `static/img` do not match the names listed above. Press `Ctrl+F5`. |
| The artisan sees "No task" | The order must be assigned to **that** artisan and the Liaison must have confirmed payment. |
| Seeding stops with a password message | Set `SEED_PASSWORD` (8 to 72 characters) in `.env`. |

---

## Known limitations

- **Payment is confirmed by hand.** There is no payment gateway; the Liaison checks the NGO's UPI app. The QR code is a fixed image, so it carries no amount or order number.
- **No CSRF tokens.** `SameSite=Lax` blocks most cross-site POSTs, but a production system should add tokens (for example Flask-WTF).
- **Logout only deletes the cookie.** A signed token cannot be cancelled before it expires.
- **`/uploads` links are public** to anyone who has the exact address.
- **The artisan page shows one task at a time** (the first assigned, paid order).
- **No reject-and-rework step.** The Liaison can approve but cannot send work back.
- **No email notifications** and no offline mode.
- Runs on Flask's development server with SQLite, which suits a demo and not a public deployment.

---

## Team and roles

| Role | Responsibility |
| --- | --- |
| Tamiya Ahmed: Database and authentication | `schema.sql`, `db.py`, `security.py`, `routes/auth.py`, seed and user scripts, `.env` configuration |
| Saloni Gupta: Frontend | `templates/`, `static/`, `routes/pages.py`, Selenium tests |
| Neha Vaid: Business logic and file storage | `services/orders.py`, `services/uploads.py`: order rules, payment steps, image checks and storage |

Work was done on separate branches per student and merged into `main`.

---


