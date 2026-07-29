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
approve or reopen. Students and parents see Approved results only. Result audit
logs are immutable and include request metadata when available.

Reports under `/api/v1/exam-results/reports/` provide student transcripts and
class, subject, and exam statistics. See `SPRINT_3.md` for routes and policy.
