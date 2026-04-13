# Django Bakery Frontend + Backend

This folder contains a Django implementation of the bakery site with template-based frontend and a working backend (models, views, URLs, admin, and tests).

## Run locally

```bash
cd django_bakery
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_catalog  # loads categories + products from bakery catalog
python manage.py createsuperuser  # optional
python manage.py runserver
```

## SMTP email and Google login setup

1. Copy `.env.example` to `.env` in this folder and fill your values.
2. For real emails, set `USE_SMTP_EMAIL=true` and provide SMTP credentials.
3. For Google login, set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.
4. In Google Cloud OAuth app, add redirect URIs:
	- `http://127.0.0.1:8000/accounts/google/login/callback/`
	- `http://localhost:8000/accounts/google/login/callback/`
5. Restart the server after changing `.env` values.

Authentication routes:

- `/auth/register/` - Sign up
- `/auth/login/` - Login (email or username + remember me)
- `/auth/verify-email/` - Email verification pending page
- `/auth/forgot-password/` - Password reset request
- `/account/dashboard/` - Protected user dashboard
- `/account/settings/` - Account settings, saved addresses, payment methods

## Add product images

1. Open Django Admin at `/admin/`.
2. Go to `Products` and edit any product.
3. Upload an image using the `image` field and save.

Uploaded files are stored in `media/products/`.

## What is included

- Template-based UI (`templates/` + `static/`)
- Backend models (`Category`, `Product`)
- URL routing and view rendering
- Django admin configuration
- Catalog seed command (`manage.py seed_catalog`)
- Test coverage for main pages
