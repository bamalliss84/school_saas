# Sprint 3.5 - Publish Results Platform

## Status

Implemented. Publication is an explicit state separate from the existing result approval workflow.

## Policy

- A result must remain `approved` before it can be published.
- Publishing never adds or changes a workflow status.
- Students and parents can read only results that are both approved and published.
- Teachers and administrators retain scoped visibility of unpublished workflow data.
- Only `school_admin` for the owning school or `super_admin` may publish or unpublish.
- Cross-tenant identifiers are resolved through scoped selectors and return 404.

## API

- `POST /api/v1/exams/{id}/publish/`
- `POST /api/v1/exams/{id}/unpublish/`
- `POST /api/v1/exams/bulk-publish/`

Single-exam and bulk publication are atomic. Publishing processes Approved results and reports published, skipped, already-published, and total counts. An exam with no Approved results is rejected. Bulk publication rolls back every exam if any selected exam fails. Optional `reason` is retained in the immutable audit trail.

## Data and audit

`ExamResult` stores `is_published`, `published_at`, and `published_by`. `ExamResultLog` records publish/unpublish actions, old/new publication values, publisher, reason, request metadata, and timestamp. Reopening an Approved published result automatically audits an unpublish transition, clears publication metadata, and then returns the result to Draft.

## Admin and integrations

Django Admin shows the published-result count and provides publish/unpublish actions. `notify_results_published` is a no-op extension point for a future notification provider. Scheduled publication is deferred until a scheduler and its operational guarantees are selected.


## Verification

The final gate completed with 203 passing core tests, 93% coverage, a clean
Ruff result, and validated OpenAPI generation with zero warnings. Django checks
and migrations passed. Temporary server verification returned 200 for live,
ready, schema, and docs; unauthenticated publish returned 401; the server was
then stopped. `check --deploy` retains the three documented development-only
warnings for HSTS, HTTPS redirect, and the placeholder secret key.
