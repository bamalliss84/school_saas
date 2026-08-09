# Sprint 4.6 — Demo Data and Real E2E Acceptance

Sprint 4.6 is a verification sprint. It adds a guarded, deterministic management command and API-driven acceptance tests without adding public endpoints or changing the frozen API contract.

## Commands

```text
backend\venv\Scripts\python.exe backend\manage.py seed_demo_school
backend\venv\Scripts\python.exe backend\manage.py seed_demo_school --reset-demo
```

The command refuses to run with `DEBUG=False` unless `--allow-non-debug` explicitly acknowledges an isolated acceptance environment. It never flushes or truncates the database. Reset deletes only schools with codes `DEMO_NOOR`/`DEMO_FUTURE` and users prefixed `demo_`, in a domain-safe order.

## Acceptance scope

- Two schools, two academic years each, terms, grades, sections, subjects and class-subject mappings.
- Single-school and multi-school teachers, parents, students, and a transferred student with historical/current contexts.
- Attendance, exams/published results, homework/submission, membership notifications, conversations/messages and announcements/receipts.
- JWT login/refresh/logout, context switching, historical read-only behavior, parent privacy, membership isolation, IDOR probes and representative error contracts.

See `DEMO_DATA.md` and `E2E_ACCEPTANCE_REPORT.md`.
