# School SaaS Stabilization Audit — Sprint 4C

## Scope

This audit was performed after repeated failure of `test_student_sees_only_published_receipt`.
The review covered the request path from JWT context resolution through permissions, query
serializer validation, announcement recipient selection, pagination, and serialization.
It also included a project-wide scan for the same class of query-filter bug.

## Root cause

The problem was not the drive letter, PostgreSQL, migrations, pagination, or recipient creation.
`AnnouncementReceipt` existed and the direct membership-scoped selector returned the published
announcement correctly.

The real cause was DRF's HTML input behavior for `BooleanField`. `request.query_params` is a
`QueryDict`; when the `unread` key was omitted, the stock field inserted `unread=False` into
`validated_data`. The view therefore silently applied the "read announcements only" filter,
which excluded the unread receipt and returned an empty list.

## Root fix

A reusable `OptionalBooleanField` was introduced in `core/serializer_fields.py`. It preserves the
three states required by query APIs:

- parameter omitted: no filter
- explicit true: true filter
- explicit false: false filter

The field was applied project-wide to optional boolean query filters in announcements,
notifications, student/teacher filters, homework, submissions, conversations, and exam types.
Regression tests verify omission and explicit false independently.

## Active Context hardening

`core/permissions.py` now reads the canonical role and tenant context from:

- `request.active_membership`
- `request.active_school`
- `request.active_role`
- `request.active_academic_year`

Legacy user fields remain only as a documented fallback for older endpoints that have not yet
completed the compatibility migration.

## Verification performed in the review environment

- Target announcement regression test: passed.
- Query boolean semantics tests: passed.
- Full `core` suite using a clean SQLite test database: 561/561 passed.
- Django system check: passed.
- `makemigrations --check --dry-run`: no changes detected.
- Python compile check for `backend/core` and `backend/config`: passed.
- `git diff --check`: passed.

PostgreSQL remains the production source of truth. The user must rerun the complete checks on the
Windows/PostgreSQL environment before commit.

## Project-wide review findings

### Confirmed strengths

- Multi-school identity and membership context are structurally present.
- New communication and announcement code is membership-scoped.
- Historical contexts are read-only except documented personal read markers.
- Transactional services and post-commit side effects are used consistently in recent sprints.
- Migrations are sequential through `0023_announcements_targeting`.
- The project has broad regression coverage across authentication, attendance, exams, homework,
  messaging, notifications, identity, and announcements.

### Remaining technical debt before Flutter freeze

A static scan still finds older endpoints and serializers using `request.user.school`,
`request.user.role`, or `request.user.academic_year`. These are currently supported by the
request-local compatibility adapter, but they should be migrated to `request.active_*` before the
Flutter API contract is frozen. This is not silently changed in Sprint 4C because a broad rewrite
would require a separate, explicitly scoped regression sprint.

Recommended next stabilization step:

`Sprint 4.5 — Active Context Migration & Architecture Freeze`

It should remove remaining legacy request-context reads from public APIs, add direct regression
coverage, and produce the frozen backend/API/Flutter contracts.
