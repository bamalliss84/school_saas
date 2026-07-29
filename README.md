# School SaaS

Multi-school Django backend.

## Local setup

1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.
3. Configure PostgreSQL environment variables using `.env.example` as a reference.
4. Run `python manage.py migrate`.
5. Run `python manage.py runserver`.

## Important

Exam result changes should be performed through `core.services.update_exam_result` so the audit log records the acting user and reason. Django Admin also records score/status changes automatically.
