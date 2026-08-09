# Architecture Audit Findings

## Result

No open Critical or High backend finding was identified in the final Windows/PostgreSQL audit.

## Fixed during stabilization

- Optional Boolean query fields now preserve omitted, true, and false as distinct states.
- Sprint 4C received regression coverage for targeting, workflows, filters, attachments, inquiry routing, and tenant isolation.

## Medium technical debt

- Older pre-active-context selectors, views, serializers, and services read request-local legacy `User` fields. The context adapter mutates these fields in memory only, so selected membership context remains effective and the complete security suite passes. These call sites should migrate incrementally to explicit context parameters; see `ACTIVE_CONTEXT_MIGRATION_REPORT.md`.

## Low / operational

- Production must provide a strong secret key, HTTPS redirect, and HSTS values.
- External delivery providers and production media/static infrastructure require deployment-specific verification.
