# Sprint 4.5 — Stabilization and Architecture Freeze

Sprint 4.5 is a stabilization pass, not a feature sprint. It verifies the multi-school active-context architecture, Sprint 4C announcements, Windows/PostgreSQL behavior, API schema, migrations, lint, coverage, and live endpoints.

The canonical request authorization inputs are `request.active_membership`, `request.active_school`, `request.active_role`, and `request.active_academic_year`. Older endpoints may still read request-local legacy `User` fields populated by the compatibility adapter; those reads are tracked in `ACTIVE_CONTEXT_MIGRATION_REPORT.md` and must not be copied into new code.

Acceptance evidence is recorded in `BACKEND_FINAL_ACCEPTANCE_REPORT.md`.
