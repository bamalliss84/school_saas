# Phase 2 — Student Attendance V1

## Backend review before implementation

The existing backend already had the canonical Attendance model, four statuses (`present`, `absent`, `late`, `excused`), one-record-per-student-per-day constraint, bulk teacher/admin writes, daily/student/class summaries, tenant scoping, and historical read-only enforcement. The implementation therefore preserves that domain model and adds only a student-self read endpoint; no attendance model or migration was added.

## Additive API

`GET /api/v1/students/me/attendance/`

- Requires active student membership context.
- Resolves the student from the authenticated user; Flutter never supplies a student id.
- Scopes to `request.active_school` and `request.active_academic_year`.
- Historical memberships can read their old academic-year attendance.
- Supports `date_from`, `date_to`, and `academic_term_id`.
- Returns student/year/terms, status counts, attendance percentage using the existing backend rule `(present + late) / total`, and daily records.

## Flutter

- Home shortcut opens Attendance without changing the approved bottom navigation.
- Summary card: attendance percentage + present/absent/late/excused counts.
- Period filter: academic year, current month, or academic term.
- Daily list + read-only detail screen.
- Offline cache is scoped by existing `CacheScope(user, membership, academic year)` and stored as a dedicated generic cached-context resource, avoiding a Drift schema migration.
- Global Offline banner/session/error behavior remains unchanged.

## Demo

`demo_student_a_01` receives deterministic August 2026 records covering every status and notes. Seeder remains idempotent via `update_or_create`.

## Verification still required on the user's Windows environment

- Django check/migration check/tests.
- Flutter analyze/test.
- Android emulator smoke: Online, filters, detail, offline cache, empty filter.
