# Sprint 4D — Multi-School Identity, Memberships & Context

Status: completed and verified.

## Architecture

`User` is a global identity. `SchoolMembership` is the authority for school and role in a request. It supports active, historical, suspended and ended states, one user/school/role tuple, one active student membership platform-wide and one default membership. `User.school`, `User.role`, `User.academic_year`, `Student.school` and profile school fields remain legacy compatibility pointers and must not authorize new code.

The JWT authentication layer resolves `X-School-Membership-ID`. The official sources for all new request-scoped code are `request.active_membership`, `request.active_school`, `request.active_role` and `request.active_academic_year`. `request.user.school`, `request.user.role` and `request.user.academic_year` are temporary Legacy Compatibility Fields supplied by a request-local adapter only; they must not authorize new code and the mutated user must never be saved. One active membership is auto-selected; multiple active memberships without a header return `409 context_required`. Foreign IDs return 404, unavailable contexts return 403, and historical contexts permit only safe methods. The active academic year is always constrained to the active school.

## APIs

- `GET /api/v1/auth/contexts/`, `GET /api/v1/auth/context/`, `POST /api/v1/auth/context/default/`.
- `/api/v1/auth/me/` includes the active context and context summary.
- Student self school/history and parent child school/history endpoints validate memberships and guardian ownership.
- `POST /api/v1/students/{id}/transfer/` is super-admin-only and calls the atomic transfer service.
- Existing student, parent, teacher, attendance, exam/result and homework endpoints inherit the request context through the compatibility bridge and remain tenant-scoped.

## Student transfer and history

`StudentEnrollment.school` is authoritative for each academic record. Database constraints permit one current enrollment and require it to be active. `transfer_student()` locks the student and current enrollment, closes the old enrollment, changes the old membership to historical, creates the new active/default membership and enrollment, updates the legacy pointer, synchronizes guardian memberships, and writes an audit event. Attendance, results, homework and files are never copied between schools. Any failure rolls back the whole transfer.

## Parent, teacher and multi-role behavior

Parent memberships derive from guarded children and can span schools. Parent history endpoints require `StudentGuardian`. A teacher may hold active teacher memberships and assignments in multiple schools; active context selects one school's assignments. The same user may hold distinct roles in the same or different schools.

## Migration 0020

Migration `0020_multischool_memberships` defensively repairs invalid current-enrollment states, creates memberships from legacy users, enrollments, assignments and guardian links without changing IDs or operational ownership, selects a logical default, then adds database constraints. Reverse is intentionally a no-op because deleting derived identity history would lose meaning.

## Admin, performance and OpenAPI

Membership admin is tenant-scoped and prevents school admins granting cross-school or super-admin membership. Student current school derives from enrollment; teacher schools are prefetched. Context and history queries use related joins/prefetching. OpenAPI documents JWT plus `X-School-Membership-ID`; context errors use the unified envelope.

## Deferred

Two-sided transfer approval, national identity matching, account merge, external SSO, district hierarchy, record sharing, file transfer, membership billing, Firebase/Flutter, removal of legacy fields, school-local code redesign and scheduled publishing remain deferred.
## Sprint 4D.1 — Consistency hardening

- Data migration 0020 resolves stale legacy student schools before adding uniqueness constraints.
- Identity synchronization services cover enrollment switches, guardian-derived parent contexts and assignment-derived teacher contexts without signals.
- Student transfer updates both Student and User legacy pointers and validates destination activity and dates before writes.
- Historical student/parent contexts expose published/closed Homework and owned submissions only.
- Header context selection performs no `last_used_at` write; explicit default selection records use.
- The legacy user adapter is request-local and must never be persisted.

Verification status is complete only after the full core suite, Coverage, Ruff, OpenAPI and server checks pass.
