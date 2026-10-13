# Test Plan

## Scope
Functional UI flows, role access, REST API status and payload validation, input validation, stock consistency, tax arithmetic, regression, and basic response-time checks.

## Test levels
- Unit/integration: pytest with isolated temporary SQLite database.
- API: Postman collection; login first to establish session cookie.
- UI: manual browser checks for login, product CRUD, inventory, bill creation, receipt printing, and report filters.
- Static analysis: SonarQube Community Build; capture real dashboard results.

## Key test cases

| ID | Scenario | Expected result | Execution status |
|---|---|---|---|
| T-01 | Correct admin login | Dashboard displayed | Pending recorded run |
| T-02 | Incorrect password | Error message; no authenticated session | Pending recorded run |
| T-03 | Cashier attempts product creation | 403 in API / denied in UI | Pending recorded run |
| T-04 | Add product with unique SKU | Product created | Pending recorded run |
| T-05 | Duplicate SKU | 409 API response | Pending recorded run |
| T-06 | Negative price or quantity | 400 API response / form validation | Pending recorded run |
| T-07 | Create bill with available stock | 201; correct totals; stock decremented | Pending recorded run |
| T-08 | Bill quantity exceeds stock | 409; no bill or stock change | Pending recorded run |
| T-09 | Cashier requests sales report | 403 | Pending recorded run |
| T-10 | Invalid report period | 400 | Pending recorded run |
| T-11 | Delete product referenced by bill | 409 | Pending recorded run |
| T-12 | Low-stock API | Only products at/below threshold returned | Pending recorded run |

## Exit criteria
All high-priority tests have been executed, failures are either fixed or documented, the test summary is based on recorded execution, and screenshots/logs are stored with the submission.
