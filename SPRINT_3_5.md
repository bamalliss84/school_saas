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


## Sprint 3.5.1 publication hardening

Publication notifications are registered with `transaction.on_commit` using an
immutable exam ID and tuple of result IDs. Bulk rollback discards every pending
callback, and post-commit notification failures are logged without reverting
published data. The stub remains a no-op.

Django Admin publication actions now keep tenant-scoped selections, catch service
validation and permission errors, and report success/error counts through the
messages framework. Teachers cannot see or execute the actions even when marked
as staff.

Migration `0018_harden_exam_result_publication` first defensively resets invalid
publication state to unpublished, then adds database constraints requiring
Approved workflow and complete publisher metadata for published results, and no
publication metadata for unpublished results.

Audit IP collection trusts `REMOTE_ADDR` by default. Set
`TRUST_X_FORWARDED_FOR=True` only behind a trusted proxy that sanitizes the
header; the first syntactically valid forwarded address is then used. Invalid
values are ignored safely. Result and audit selectors join `published_by` to keep
published lists bounded without N+1 queries.


### Sprint 3.5.1 verification

The hardening gate completed with 219 passing core tests, 93% coverage, clean
Ruff output, and validated OpenAPI generation with zero warnings. Migration 0018
was applied successfully. The temporary server returned 200 for live, ready, and
schema checks, then stopped with zero runserver processes remaining.
