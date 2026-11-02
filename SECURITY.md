# Security Policy

## Supported Versions

We actively maintain and provide security updates for the latest `main` branch of **Saminel Bakery**.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Security Focus Areas

Because **Saminel Bakery** serves as an open-source reference template for storefront e-commerce, order management, and offline-first Point-of-Sale (POS) workflows, we prioritize security across the following areas:

* **Authentication & Brute-Force Protection (`bakery/auth_views.py`):** Account lockout after repeated failed login attempts (`MAX_LOGIN_ATTEMPTS`), email verification tokens, and `SecurityEvent` audit logging for new device logins, password changes, and lockouts.
* **Client-Side Storage & Sync (`IndexedDB` / `LocalStorage`):** Preventing unauthorized state tampering, sensitive data leakage, and race conditions during offline-to-online order synchronization (`/api/orders/sync/`).
* **Input Validation & Sanitization:** Protecting customer checkout forms, order notes, address management, and POS product search filters against Cross-Site Scripting (XSS), CSRF, and injection vulnerabilities.
* **Role-Based Access Control (RBAC):** Enforcing strict separation between `Regular`, `Moderator`, and `Admin` user profiles across storefront views, moderator consoles, and staff POS interfaces.
* **Dependency & Supply Chain Hygiene:** Keeping Python (`requirements.txt`) and frontend assets audited and free of known vulnerabilities.

## Reporting a Vulnerability

We take the security of this codebase seriously. If you discover a security vulnerability, **please do not open a public GitHub issue.**

Instead, please report it privately using one of the following methods:

1. **GitHub Private Vulnerability Reporting:** Navigate to the **Security** tab of this repository and click **"Report a vulnerability"** to open a private advisory.
2. **Direct Email:** Send a detailed report to **bringoxin@gmail.com** with the subject line `[SECURITY] Saminel Bakery Vulnerability Report`.

### What to Include in Your Report

* A clear description of the vulnerability and its potential impact.
* Step-by-step instructions or proof-of-concept (PoC) code to reproduce the issue.
* Affected files, endpoints, components, or browser environments.
* Any suggested mitigations or fixes (if available).

### Response Timeline

* **Acknowledgment:** Within **48 hours** of receiving your report.
* **Status Update & Triage:** Within **5 business days** with an assessment and expected resolution timeline.
* **Disclosure:** Once a patch is verified and merged, we will coordinate public disclosure and credit your contribution (unless you prefer to remain anonymous).
