# ShopStock — Inventory and Billing System

**Organization:** Vistara Labs Pvt. Ltd. (academic project context)  
**SRS project:** Inventory and Billing System for Shops  
**Stack:** Python, Flask, SQLite, HTML, CSS, JavaScript, pytest, Postman, SonarQube

A runnable starter application that demonstrates product CRUD, stock tracking, low-stock alerts, tax-aware billing, receipts, role-based access, sales summaries, REST APIs, and QA artefacts.

## 1. Prerequisites

- Python 3.10 or newer
- Postman (optional, for API testing)
- Git (for version control)
- SonarQube Community Build and SonarScanner (optional, for static analysis)

## 2. Run locally on Windows

Open PowerShell in this folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000.

**Demo logins (local demonstration only):**
- Admin: `admin` / `Admin@123`
- Cashier: `cashier` / `Cashier@123`

The application creates `shopstock.db` and seeds a few demo products on first run. To reset demo data, stop the server and delete `shopstock.db`; it will be recreated at startup.

For a Unix-like shell:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## 3. Implemented functions

- Login/logout with hashed demo passwords and admin/cashier role checks.
- Product listing and search; admin-only create, update and delete.
- Stock overview and configurable low-stock thresholds.
- Billing with server-side price/tax calculation, stock validation, receipt history, and stock deduction.
- Admin sales report with daily/weekly/monthly period filters and top-selling products.
- JSON API endpoints for products, low-stock inventory, bills, and sales reports.
- Basic security headers and server-side validation.

## 4. REST API summary

All API requests except login require a logged-in session. In Postman, run the login request first and keep cookies enabled. Admin-only APIs return 403 for a logged-in cashier.

| Method | Endpoint | Access | Success / common errors |
|---|---|---|---|
| GET | `/api/products` | Admin or cashier | 200 |
| POST | `/api/products` | Admin | 201; 400 invalid data; 409 duplicate SKU |
| GET | `/api/products/<id>` | Admin | 200; 404 |
| PUT | `/api/products/<id>` | Admin | 200; 400 invalid data; 404; 409 duplicate SKU |
| DELETE | `/api/products/<id>` | Admin | 204; 404; 409 if used by a bill |
| GET | `/api/inventory/low-stock` | Admin or cashier | 200 |
| GET | `/api/bills` | Admin or cashier | 200 |
| POST | `/api/bills` | Admin or cashier | 201; 400 invalid request; 409 insufficient stock |
| GET | `/api/reports/sales?period=daily` | Admin | 200; 400 invalid period |

The API uses Flask session-cookie authentication, not bearer JWT. Do not send API requests before logging in. Exact error responses should be verified during execution.

## 5. Automated tests

```powershell
python -m pytest -v
```

Tests use a temporary SQLite database and cover authentication, product CRUD, duplicate SKU, role permissions, billing/tax calculations, stock consistency, and invalid report periods.

## 6. Postman

Import `postman/ShopStock.postman_collection.json` into Postman. Set `baseUrl` to `http://127.0.0.1:5000`. Run **Admin login** first. The collection includes product, inventory, billing and report requests with post-response assertions. Cookie handling must be enabled in Postman.

Some requests change data. Use a local demo database and avoid running destructive requests against production data. The PUT and DELETE examples use `productId` or the product ID saved by the create request.

## 7. Static analysis with SonarQube

The repository includes `sonar-project.properties`. Start SonarQube Community Build and configure SonarScanner for your environment, then run a scan from this directory, for example:

```bash
sonar-scanner -Dsonar.host.url=http://localhost:9000 -Dsonar.token=YOUR_TOKEN
```

Use a token created in your local SonarQube instance; do not commit it. Record the actual issues, metrics and Quality Gate shown by your scan. A configured file is not evidence that a scan has already passed.

## 8. Version control workflow

```bash
git init
git add .
git commit -m "Initial ShopStock inventory and billing application"
git branch -M main
# Create an empty repository on your Git hosting service, then add its URL:
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

Suggested branch convention: `feature/product-crud`, `feature/billing`, `test/api-suite`, `fix/stock-validation`. Use pull requests and review before merging.

## 9. Security and production limitations

This is a local educational demonstration, not a production-ready retail system. Before deployment: set a strong random `SECRET_KEY`; add CSRF protection to browser forms; use HTTPS; add login rate limiting and audit logging; review session and cookie settings; add database migrations and backups; verify tax/legal rules with the applicable requirements; add stronger concurrent stock-update transaction handling; configure CSP and other security headers; and test authorization thoroughly. Demo passwords are public by design and must be changed.

## 10. QA and project documentation

See `docs/PROJECT_PLAN.md`, `docs/API_TESTING_REPORT.md`, `docs/QUALITY_REPORT_TEMPLATE.md`, `docs/RISK_REGISTER.md`, `docs/DEFECT_LOG.md`, and `docs/TEST_PLAN.md`. Populate result fields from real test runs and the actual SonarQube dashboard; do not claim unexecuted tests passed.
