# Demo Data

All records are synthetic and development-only. The shared password is `DemoPass123!`; it is not a production credential.

## Schools

- `DEMO_NOOR`: مدرسة النور التجريبية.
- `DEMO_FUTURE`: مدرسة المستقبل التجريبية.

Each school has previous/current years, Term 1, Grades 6/7, Sections A/B, and Mathematics/Arabic/Science/English.

## Users

| Username | Role / context |
|---|---|
| `demo_super_admin` | Super admin |
| `demo_school_a_admin` | School A admin |
| `demo_school_b_admin` | School B admin |
| `demo_teacher_a` | School A teacher |
| `demo_teacher_b` | School B teacher |
| `demo_teacher_multi` | Active teacher memberships in A and B |
| `demo_parent_a` | Parent of two School A students |
| `demo_parent_multi` | Parent with current B and historical A memberships |
| `demo_student_a_01` … `demo_student_a_10` | School A students |
| `demo_student_b_01` … `demo_student_b_10` | School B students |
| `demo_student_transferred` | Historical A, current B |

Use `/api/v1/auth/contexts/` after login and send `X-School-Membership-ID`. The multi-school teacher deliberately exercises assignment separation between A and B. The transferred student has old A attendance/announcement history and independent current B data; no operational record is copied between tenants.

## Scenario map

- School A Grade 6/A Mathematics: Teacher A, students, attendance, published homework/submission, quiz/result and announcement.
- School A Grade 7/A Science: multi-school teacher.
- School B Grade 6/B Mathematics: multi-school teacher, students and independent homework.
- School B Grade 7/A English: Teacher B.
- Synthetic notification and School Support conversation/message records are membership-scoped.

## Seed and reset

```text
set DJANGO_DEBUG=True
backend\venv\Scripts\python.exe backend\manage.py seed_demo_school
backend\venv\Scripts\python.exe backend\manage.py seed_demo_school --reset-demo
```

Running seed twice does not duplicate the dataset. Never use this password or dataset in production.
