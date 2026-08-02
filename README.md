# School SaaS

Multi-tenant school management backend built with Django and Django REST Framework.

## Local setup

1. Create the virtual environment at `backend\venv`.
2. Install runtime dependencies:

   ```text
   backend\venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. Copy values from `.env.example` into your local environment. Never commit `.env`.
4. Start PostgreSQL and run:

   ```text
   backend\venv\Scripts\python.exe backend\manage.py migrate
   backend\venv\Scripts\python.exe backend\manage.py check
   backend\venv\Scripts\python.exe backend\manage.py runserver 127.0.0.1:8000 --noreload
   ```

## API

New clients should use `/api/v1/`. Existing `/api/` routes remain temporarily for compatibility.

- Schema: `/api/schema/`
- Swagger: `/api/docs/`
- ReDoc: `/api/redoc/`
- Versioned schema: `/api/v1/schema/`
- Versioned docs: `/api/v1/docs/`

Documentation is available in development. In production it requires an authenticated staff user.

## Health checks

- `/health/live/`: Django process liveness.
- `/health/ready/`: database and migrations readiness.
- `/api/v1/health/`: versioned liveness alias.

Health responses intentionally contain no database names, credentials, or environment details.

## Quality

Install development dependencies:

```text
backend\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Run:

```text
backend\venv\Scripts\python.exe backend\manage.py test core
backend\venv\Scripts\python.exe -m ruff check backend/core backend/config
backend\venv\Scripts\python.exe -m coverage run backend/manage.py test core
backend\venv\Scripts\python.exe -m coverage report
```

`DEBUG` defaults to `False`; set `DJANGO_DEBUG=True` explicitly for local development. `python backend/manage.py check --deploy` retains three expected development-environment warnings until a production SECRET_KEY, HTTPS redirect, and HSTS are configured through environment variables.

## Static and media

Django serves media only in local development when `DEBUG=True`. Production must serve static/media through infrastructure designed for that purpose. School logos and operational media are not tracked in Git.

## Important architecture

- Every operational queryset must remain scoped by school and role.
- Student academic history is stored in `StudentEnrollment`.
- Teacher scope comes from `TeacherAssignment`.
- Exam result changes must use `core.services.update_exam_result` so `ExamResultLog` records the actor and reason.
- `ExamResultLog` is read-only in Django Admin.
## Exams and results

Sprint 3 provides versioned CRUD for exam types, exams, and results, plus
atomic bulk grading and explicit submit/approve/reject/reopen actions. Teachers
can edit Draft results for their assignments; only school or super admins can
approve or reopen. Students and parents see results only after both approval and explicit publication. Result audit
logs are immutable and include request metadata when available.

Reports under `/api/v1/exam-results/reports/` provide student transcripts and
class, subject, and exam statistics. See `SPRINT_3.md` for routes and policy.


## Result publication

Sprint 3.5 separates approval from publication. School administrators and super
administrators can atomically publish or unpublish an exam, and can bulk-publish
multiple exams. Publishing reports non-Approved results as skipped, and bulk
failures roll back the request. Reopen automatically unpublishes before returning
a result to Draft. Published state is audited. See `SPRINT_3_5.md`.


## Publication hardening

Publication notifications run only after a successful database commit and use
non-sensitive immutable IDs. Configure `TRUST_X_FORWARDED_FOR=True` only when a
trusted reverse proxy sanitizes that header; otherwise audit logs use the direct
`REMOTE_ADDR`. Migration 0018 enforces publication metadata consistency at the
database layer.

## Homework and submissions

Sprint 4A adds tenant-scoped Homework and HomeworkSubmission workflows under
`/api/v1/`, including atomic publish/close/grade operations, multipart
attachments, aggregate reports, audit records, and Django Admin actions. Files
are validated by configurable size, count, extension and MIME policies. Storage
deletion and future notification hooks run only after database commit. The workflow hooks now create membership-scoped Notifications after commit. Announcements and targeting remain deferred to Sprint 4C.
## Multi-school context (Sprint 4D)

A user can belong to multiple schools and roles through `SchoolMembership`. Canonical school APIs accept `X-School-Membership-ID`; it is optional only when one active context exists. The official sources for new request-scoped code are `request.active_membership`, `request.active_school`, `request.active_role`, and `request.active_academic_year`. The corresponding `request.user` school, role, and academic-year values are temporary Legacy Compatibility Fields, not authorization sources. Multiple active contexts without the header return `409 context_required`. Historical memberships are read-only. Discover contexts at `/api/v1/auth/contexts/`. Student transfers are atomic and super-admin-only in this release. See `SPRINT_4D.md`.

## Sprint 4D.1 consistency hardening

Membership synchronization is centralized in `core.services.identity` without signals. The current active student enrollment controls the active/default student membership plus legacy Student/User school and academic-year pointers. Parent memberships reflect current and historical guarded children; teacher synchronization creates assignment-derived memberships without downgrading explicit active memberships. Historical contexts include published/closed Homework and owned submissions from the selected school, while all writes remain forbidden. Ordinary Header-based requests do not update `last_used_at`; explicit default-context selection does. Authentication's legacy user mutation is in-memory and request-local only.


## Sprint 4B communications

Membership-scoped notifications, homework completion/dashboard APIs, conversations, messages, safe attachments, teacher broadcasts, and the School Inbox are available under `/api/v1/`. Clients must select a context and send `X-School-Membership-ID`; feeds and unread badges are isolated to that membership. Message and workflow notifications are created after database commit. Historical contexts are read-only except documented personal read markers. See `SPRINT_4B.md` for routes, DTOs, privacy rules, and the Flutter context-switch flow. Announcements and targeting are planned for Sprint 4C.


## Sprint 4B.1 privacy hardening

Guardian and homework conversations are private two-party threads; the platform never creates parent group chats. School Support creation notifies active same-school administrators after commit using a safe preview. Attachment batches and support transitions are atomic. Broadcast actions accept only documented routes and scoped parameters, while notification payloads reject secrets recursively. Authorization is enforced again inside specialized messaging services. The original communication schema remains in migration 0021; migration 0022 applies the privacy-hardening constraints without rewriting an already-applied migration.
