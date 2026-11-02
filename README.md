# Saminel Bakery (Saminel Flame) — Open-Source E-Commerce & Offline-First POS Template

**Saminel Bakery** (`Saminel Flame`) is a full-stack open-source storefront and Point-of-Sale (POS) web application designed for local bakeries, cafes, and small-to-medium food businesses. Built with Django and a modular, zero-heavy-framework frontend (`HTML5`, `CSS3`, `Vanilla ES6+ JavaScript`, and `IndexedDB`), it provides a resilient reference architecture for digitizing product catalogs, role-based staff operations, and offline-first order workflows without expensive proprietary SaaS subscriptions.

---

## Key Features

* **Interactive Storefront & POS Product Grid:** Responsive, touch-friendly product cards and a dedicated `/pos/` counter terminal with category filtering, instant search, and quick-add cart actions.
* **Offline-First Architecture (`IndexedDB` + `LocalStorage`):** Client-side cart persistence, catalog caching, and an offline order queue (`saminel_pos_db`) that allows counter staff and customers to queue orders during unstable internet connectivity and automatically syncs with `/api/orders/sync/` once online.
* **Role-Based Access Control (RBAC) & Security Auditing:** Built-in user profiles supporting `Regular`, `Moderator`, and `Admin` roles, account lockout protection after failed login attempts, email verification, Google OAuth2 (`django-allauth`), and automated `SecurityEvent` audit logging.
* **Complete Order & Account Management:** Saved customer shipping addresses (defaulting to Ghana), multiple payment method records (`Card`, `Mobile Money`, `Bank Transfer`, `Cash on Delivery`), and order lifecycle tracking (`Pending`, `Processing`, `Completed`, `Cancelled`).
* **One-Command Catalog Seeding:** Includes `python manage.py seed_catalog` with curated bakery categories and product imagery out of the box.

---

## Tech Stack

* **Backend:** Python 3, Django 5.1+, SQLite / PostgreSQL-ready ORM, `django-allauth`, `bcrypt`, `PyJWT`
* **Frontend:** Django Templates, Custom Responsive CSS3 Grid & Flexbox UI, Vanilla JavaScript (ES6+)
* **Offline Storage & Sync:** Browser `IndexedDB` API (`saminel_pos_db`) & `LocalStorage` fallback with automatic online background sync
* **CI & Security:** GitHub Actions (`.github/workflows/django.yml`), `SecurityEvent` audit trail, CSRF & input validation

---

## Project Structure

```text
Saminel_bakery/
├── .github/workflows/       # GitHub Actions CI pipeline for Django tests
├── bakery/                  # Core Django app (models, views, RBAC auth, POS & sync APIs)
│   ├── management/commands/ # Custom CLI commands (seed_catalog)
│   ├── migrations/          # Database schema migrations
│   ├── admin.py             # Admin panel configuration
│   ├── auth_backends.py     # Custom email/username authentication backend
│   ├── auth_views.py        # RBAC, login lockout, verification & moderator console views
│   ├── models.py            # Category, Product, UserProfile, Address, PaymentMethod, Order, SecurityEvent
│   ├── urls.py              # Storefront, POS, Cart, Sync API, and Auth routes
│   └── views.py             # Storefront, POS terminal, Cart, and IndexedDB order sync endpoints
├── bakery_site/             # Django project settings and root URL configuration
├── media/                   # Product and user profile imagery
├── static/bakery/           # Modular CSS3 styles, branding assets, and offline_pos.js (IndexedDB engine)
├── templates/               # Storefront, POS terminal, Cart, and Auth HTML templates
├── LICENSE                  # MIT License
├── README.md                # Project documentation
├── SECURITY.md              # Vulnerability reporting and security policy
├── manage.py                # Django management entrypoint
└── requirements.txt         # Python dependencies
```

---

## Getting Started

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/Bringox123/Saminel_bakery.git
cd Saminel_bakery
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Initialize Database & Seed Catalog

```bash
python manage.py migrate
python manage.py seed_catalog      # Loads bakery categories and products
python manage.py createsuperuser   # Optional: create an admin user
python manage.py runserver
```

Open `http://127.0.0.1:8000` in your browser.

---

## Key Application Routes

* `/` — Storefront home & featured bakery items
* `/catalog/` — Full categorized bakery catalog with instant cart actions
* `/pos/` — **Offline-First Staff POS Terminal** with custom product grid, category filters, and IndexedDB order queue
* `/cart/` — Interactive shopping cart and offline-resilient checkout
* `/api/orders/sync/` — JSON endpoint for synchronizing queued offline `IndexedDB` orders
* `/auth/login/` & `/auth/register/` — Authentication with brute-force lockout protection
* `/account/dashboard/` & `/account/settings/` — Customer order history, saved addresses, and payment methods
* `/account/moderator/` — Role-protected Moderator console

---

## SMTP Email & Google OAuth Setup

1. Copy `.env.example` to `.env` in the project root and fill in your credentials.
2. For live transactional emails, set `USE_SMTP_EMAIL=true` and configure your SMTP variables.
3. For Google OAuth login, set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`, and register the callback URIs:
   * `http://127.0.0.1:8000/accounts/google/login/callback/`
   * `http://localhost:8000/accounts/google/login/callback/`

---

## Running Tests

```bash
python manage.py test
```

---

## Security

Security and data integrity are core priorities for retail and order-processing templates. Please review [SECURITY.md](SECURITY.md) for supported versions, security focus areas, and private vulnerability reporting instructions.

---

## Maintainer

* **Reginald Aaron Dobeng** ([@Bringox123](https://github.com/Bringox123)) — *Primary Maintainer & UI/UX Architect*

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
