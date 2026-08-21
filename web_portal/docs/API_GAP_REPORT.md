# School Admin Web Portal — API Gap Report (W0)

**Date:** 2026-08-21  
**Baseline Commit:** `9ea9ecd582f8c8bcdabc11510b19d2cbfec63520`  
**Author:** Antigravity Agent  
**Target Execution:** School Admin Web Portal Implementation Phases

---

## 1. Executive Summary

This report identifies all functional and technical gaps in the existing Django REST Framework backend relative to the requirements of the School Admin Web Portal.

Current production backend capabilities strongly support **Authentication & Context Resolution**, **Timetable Administration**, **Attendance Oversight**, **Homework Management**, **Exams & Results Lifecycle**, and **Communications & School Support**.

However, the School Admin Web Portal requires dedicated customer-facing APIs for **Academic Master-Data CRUD**, **People Management Write Operations**, a **Unified Dashboard KPI Endpoint**, and a **Validated Excel Import/Export Center**.

Under the non-negotiable rules of Phase W0/W1:
1. **No Backend changes or migrations are made in W0/W1.**
2. All identified gaps are documented here and scheduled for **Phase W2 (Backend School Admin Enablement)** and **Phase W6 (Excel Import/Export Foundation)**.

---

## 2. Detailed Gap Catalog by Domain

### Gap Group A: Academic Master-Data CRUD (Scheduled for Phase W2 / W4)

Currently, the backend defines models for `AcademicYear`, `AcademicTerm`, `Classroom`, `Section`, `Subject`, and `ClassSubject`, but exposes them only through read-only brief serializers or the internal Django Admin interface (`/admin/`). School Admins need full tenant-scoped REST endpoints.

| Domain Entity | Missing Operations | Target URL Pattern | Security / Tenancy Rule |
|---|---|---|---|
| **AcademicYear** | List, Create, Update, Set Active, Close | `/api/v1/academic-years/`, `/api/v1/academic-years/<pk>/` | Scope by `request.active_school`. Enforce exactly one active academic year per school. Historical context is read-only. |
| **AcademicTerm** | List, Create, Update, Delete | `/api/v1/academic-terms/`, `/api/v1/academic-terms/<pk>/` | Validate `academic_year` belongs to `active_school`. Date ranges must be bounded within year dates. |
| **Classroom** | List, Create, Update, Delete | `/api/v1/classrooms/`, `/api/v1/classrooms/<pk>/` | Scope by `active_school`. Prevent deletion if active enrollments or timetable entries exist. |
| **Section** | List, Create, Update, Delete | `/api/v1/sections/`, `/api/v1/sections/<pk>/` | Scope by `active_school`. Validate classroom FK belongs to tenant. |
| **Subject** | List, Create, Update, Delete | `/api/v1/subjects/`, `/api/v1/subjects/<pk>/` | Scope by `active_school`. Unique code per school. |
| **ClassSubject** | List, Create, Update, Delete | `/api/v1/class-subjects/`, `/api/v1/class-subjects/<pk>/` | Ensure classroom and subject belong to `active_school`. |

---

### Gap Group B: People Management CRUD (Scheduled for Phase W2 / W5)

The current backend has read-only student endpoints (`/api/v1/students/`) and user-profile self-reads (`teachers/me/*`, `parents/me/*`), but lacks administrative write interfaces for school staff and students.

| Domain Entity | Missing Operations | Target URL Pattern | Security / Tenancy Rule |
|---|---|---|---|
| **Student** | Create, Update, Deactivate | `/api/v1/students/`, `/api/v1/students/<pk>/` | Create student record, user account, and initial `StudentEnrollment` atomically in `transaction.atomic`. |
| **StudentEnrollment** | List, Enroll, Promote, Transfer Status | `/api/v1/student-enrollments/`, `/api/v1/student-enrollments/<pk>/` | Enforce one `is_current=True` active enrollment per student. Automatically synchronize student's active `SchoolMembership`. |
| **Parent / Guardian** | List, Create, Update | `/api/v1/parents/`, `/api/v1/parents/<pk>/` | Scope to `active_school`. Automatically synchronize parent `SchoolMembership` on child changes. |
| **StudentGuardian Link** | List, Link, Unlink, Set Primary | `/api/v1/student-guardians/`, `/api/v1/student-guardians/<pk>/` | Validate student and parent belong to school. Re-sync parent membership on changes. |
| **Teacher** | List, Create, Update, Deactivate | `/api/v1/teachers/`, `/api/v1/teachers/<pk>/` | Create teacher record, user account, and active `SchoolMembership`. |
| **TeacherAssignment** | List, Create, Update, Delete | `/api/v1/teacher-assignments/`, `/api/v1/teacher-assignments/<pk>/` | Validate teacher, classroom, section, subject belong to `active_school` and `active_academic_year`. |

---

### Gap Group C: Unified Dashboard Aggregation (Scheduled for Phase W2 / W3)

Currently, the web client would need to make 6+ separate API calls to gather dashboard metrics, creating unnecessary network overhead and partial failures.

| Gap Identifier | Description | Target URL Pattern | Required Aggregate Metrics |
|---|---|---|---|
| **GAP-DASH-01** | Unified School Admin Dashboard KPI Endpoint | `/api/v1/dashboard/admin/` | Total enrolled students, total active teachers, active classrooms/sections count, today's attendance summary (percentage, present, absent, late, not recorded), pending exam results awaiting approval, active published homework count, unread school inbox tickets, timetable configuration health status. |

---

### Gap Group D: Validated Excel Import / Export Center (Scheduled for Phase W2 / W6)

The web portal requires bulk data operations for onboarding and semester transitions. Immediate table writes from uploaded files are strictly forbidden.

| Gap Identifier | Description | Target Pipeline | Required Technical Behavior |
|---|---|---|---|
| **GAP-EXCEL-01** | Excel Import Staging & Validation Pipeline | `/api/v1/imports/upload/`<br>`/api/v1/imports/<job_id>/preview/`<br>`/api/v1/imports/<job_id>/commit/`<br>`/api/v1/imports/<job_id>/errors/` | Step 1: Upload XLSX file & generate `ImportJob`.<br>Step 2: Dry-run validate each row with strict schema, reference resolution, and duplicate detection.<br>Step 3: Return preview statistics and row-level validation errors.<br>Step 4: Explicit atomic commit with audit logging.<br>Entities: Students + Enrollments, Parents + Guardians, Teachers, Classrooms, Sections, Subjects, Assignments. |
| **GAP-EXCEL-02** | Scoped Excel Data Export Engine | `/api/v1/exports/students/`<br>`/api/v1/exports/attendance/`<br>`/api/v1/exports/results/`<br>`/api/v1/exports/timetable/`<br>`/api/v1/exports/homework/` | Generates standardized XLSX files strictly scoped to `request.active_school` and `request.active_academic_year`. Respects field privacy and historical read-only filters. |

---

### Gap Group E: School Profile & Branding Settings (Scheduled for Phase W2 / W14)

| Gap Identifier | Description | Target URL Pattern | Required Technical Behavior |
|---|---|---|---|
| **GAP-SET-01** | School Profile & Branding API | `/api/v1/school/profile/` | Read and update school name, phone, email, address, logo, and primary branding color under active school context. |

---

## 3. Web Portal Phase Mapping & Readiness

| Web Phase | Target Feature Area | Backend Dependency Status | Action in Current Roadmap |
|---|---|---|---|
| **W0** | API Audit & Gap Analysis | Complete | Deliver matrix and gap report (Done). |
| **W1** | Functional Web Foundation | `SUPPORTED_NOW` (Auth, Contexts, Session, Shell, Guards, Indicators) | Implement React application in `web_portal/`. |
| **W2** | Backend School Admin Enablement | Planned Gap Resolution | Implement backend CRUD, dashboard API, and tests in Phase W2. |
| **W3** | Real Admin Dashboard | Dependent on W2 `dashboard/admin/` | Consume real aggregate metrics. |
| **W4** | Academic Structure | Dependent on W2 Academic CRUD | Build academic setup UI. |
| **W5** | People Management | Dependent on W2 People CRUD | Build student/teacher/parent management UI. |
| **W6** | Excel Import / Export Center | Dependent on W2/W6 Import Pipeline | Build multi-step import wizard and export center. |
| **W7–W12** | Timetable, Attendance, Homework, Exams, Communications, Reports | `SUPPORTED_NOW` in existing backend | Build respective feature modules. |

---

## 4. Conclusion & Recommendations

1. **W1 Can Proceed Immediately:** All features required for W1 (Login, JWT session, token refresh, `auth/me`, `auth/contexts`, `X-School-Membership-ID`, 409 handling, historical read-only state, role guards, and application shell) are **100% `SUPPORTED_NOW`** in the existing backend.
2. **Strict tenet isolation in future Backend W2:** All new CRUD endpoints added in W2 must authorize exclusively from `request.active_membership`, `request.active_school`, and `request.active_academic_year`, and never from client-supplied school IDs or legacy user fields.
3. **No Unofficial APIs:** Web Portal UI will strictly avoid inventing non-existent backend endpoints or attempting to write directly to unapproved resources.
