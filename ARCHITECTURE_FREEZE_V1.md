# Backend Architecture Freeze V1

## Frozen concepts

- `User` is a global identity; `SchoolMembership` is the authorization context.
- Operational data is tenant-scoped by school. Out-of-scope object access should return 404.
- `StudentEnrollment` is the source of student school and academic history.
- `TeacherAssignment` is the source of teacher academic scope.
- Historical context is read-only except documented personal read markers.
- Exam approval and publication are separate states; changes use the result services and audit log.
- Notifications and conversation participation are membership-scoped.
- Announcement delivery is represented by immutable membership-scoped receipts.
- Workflow side effects and storage deletion run after successful commit using immutable IDs or primitive values.

## Compatibility boundary

`User.school`, `User.role`, and `User.academic_year` remain temporary compatibility fields. New APIs and services must not authorize from them. Removing them is outside Freeze V1.

## Deferred

Scheduled delivery, external push/email/WhatsApp providers, production storage, production secrets/TLS, Flutter, and new business modules are not part of this freeze.
