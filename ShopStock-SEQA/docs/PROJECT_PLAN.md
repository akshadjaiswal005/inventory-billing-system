# Project Plan — ShopStock

## Project objective
Build a small web application that supports product catalog management, inventory tracking, billing, receipt generation, and sales reports, following the Inventory and Billing System SRS.

## AI-assisted planning record
AI was used as a planning assistant to break the SRS into modules, propose test cases, draft documentation, and create a starter implementation. All generated code and requirements must be reviewed by the project team, executed locally, and validated with tests; AI output is not accepted as proof of correctness.

## Agile approach
Use one-week iterations with a short planning session, daily progress check, end-of-week demo, and retrospective. Maintain the backlog in GitHub Issues, GitLab Issues, or a local issue tracker.

| Sprint | Goal | Deliverables | Acceptance criteria |
|---|---|---|---|
| 1 | Foundation and access | Repository, Flask app, login, roles, initial database | Admin and cashier can log in; restricted pages reject wrong roles |
| 2 | Product and inventory | Product CRUD, search, stock view, low-stock alerts | Unique SKU; invalid prices/quantities rejected; threshold status correct |
| 3 | Billing and reports | Bill creation, tax calculation, receipts, reports | Bill totals correct; stock reduced only on successful bill; reports admin-only |
| 4 | Quality and handover | pytest suite, Postman collection, SonarQube scan, defect/risk logs, final report | Evidence collected; known limitations documented; run instructions verified |

## Backlog (sample)

| ID | User story | Priority | Acceptance test |
|---|---|---|---|
| US-01 | As an admin, I can add/edit/delete products | High | Valid CRUD works; duplicate SKU is rejected |
| US-02 | As a cashier, I can browse available products | High | Product list loads after authentication |
| US-03 | As a cashier, I can generate a tax-aware bill | High | Subtotal, tax and total are correct |
| US-04 | As a shop user, I can see stock status | High | Low-stock products are flagged |
| US-05 | As an admin, I can review sales summaries | Medium | Daily/weekly/monthly summaries are returned |
| US-06 | As a QA engineer, I can rerun API tests | High | Postman collection and automated tests are versioned |

## Definition of Done
- Requirement and acceptance criteria are reviewed.
- Code is committed on a feature branch and reviewed.
- Unit/API tests are run; failures are logged.
- Static analysis is run and findings reviewed.
- No known critical defect is hidden; remaining defects are documented.
- Documentation and evidence are updated.

## Version-control conventions
Use `main` for stable code, short-lived feature/fix/test branches, descriptive commit messages, and pull requests. Never commit secrets, tokens, virtual environments, or local databases.
