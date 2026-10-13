# API Testing Report — ShopStock

**Organization:** Vistara Labs Pvt. Ltd.  
**Project:** Inventory and Billing System for Shops  
**Tool:** Postman  
**Base URL (local):** `http://127.0.0.1:5000`

## Objective
Validate REST API methods, status codes, JSON response structure, access permissions, invalid input handling, and business rules for product, inventory, billing, and sales report endpoints.

## Collection
Import `../postman/ShopStock.postman_collection.json`. Run Admin login first and retain the Postman session cookie. For role-negative tests, log in as cashier in a separate run/session.

## Endpoints

| Method | Endpoint | Expected result |
|---|---|---|
| GET | `/api/products` | 200 and JSON array |
| POST | `/api/products` | 201; 400 invalid data; 409 duplicate SKU |
| GET | `/api/products/{id}` | 200; 404 when absent |
| PUT | `/api/products/{id}` | 200; 400 invalid data; 404 absent; 409 duplicate SKU |
| DELETE | `/api/products/{id}` | 204; 404 absent; 409 if referenced by bill |
| GET | `/api/inventory/low-stock` | 200 and JSON array |
| GET | `/api/bills` | 200 and JSON array |
| POST | `/api/bills` | 201; 400 malformed request; 409 insufficient stock |
| GET | `/api/reports/sales?period=daily` | 200; invalid period returns 400 |

## Validation checks
- HTTP status matches endpoint contract.
- Response body is valid JSON where a body is expected.
- Product creation returns a unique ID and submitted values.
- Bill subtotal, tax, and total are consistent with product price and tax rate.
- Successful billing decrements stock; rejected billing does not change stock.
- Role restrictions are enforced.

## Results summary — complete after execution

| Metric | Actual result |
|---|---|
| Planned cases | Record count from executed collection / test plan |
| Executed | Not yet recorded |
| Passed | Not yet recorded |
| Failed | Not yet recorded |
| Blocked | Not yet recorded |
| Pass rate | Calculate passed / executed × 100 |

## Recommendations
Use stable test data; separate positive, negative, and authorization tests; keep secrets out of exports; assert exact status codes and key response fields; rerun the collection after code changes; preserve screenshots and Postman test output as evidence. Do not mark the report as passed until actual requests have been executed.
