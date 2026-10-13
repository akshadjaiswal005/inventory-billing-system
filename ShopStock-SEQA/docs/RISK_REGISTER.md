# Risk Register

| ID | Risk | Likelihood | Impact | Mitigation | Owner / status |
|---|---|---|---|---|---|
| R-01 | Demo credentials or weak secret used outside local demo | Medium | High | Replace credentials, use environment secret, review session config | Developer — Open |
| R-02 | Unauthorized user reaches admin-only functions | Medium | High | Test role checks for every protected endpoint and page | QA — Open until verified |
| R-03 | Concurrent sales oversell available stock | Medium | High | Add atomic conditional stock updates / stronger DB transaction handling and concurrency tests | Developer — Known limitation |
| R-04 | Tax configuration does not match applicable GST rules | Medium | High | Confirm rates and invoicing requirements with authoritative requirements before real use | Product owner — Open |
| R-05 | Data loss due to missing backup/restore process | Medium | High | Schedule backups and test restoration | Operations — Open |
| R-06 | API tests change or delete test records | Medium | Medium | Use a disposable local DB and dedicated test data | QA — Mitigate by procedure |
| R-07 | AI-generated code contains unrecognized defects | Medium | High | Human review, automated tests, static analysis, and security review | Team — Ongoing |
| R-08 | SonarQube/Postman findings are reported without actual execution | Low | High | Keep result fields pending until screenshots/logs exist | QA — Process control |
