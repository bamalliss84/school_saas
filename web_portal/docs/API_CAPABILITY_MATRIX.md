# School Admin Web Portal — API Capability Matrix (W0)

**Date:** 2026-08-21  
**Baseline Commit:** `9ea9ecd582f8c8bcdabc11510b19d2cbfec63520`  
**Scope:** Functional audit of Backend API capabilities for School Admin Web Portal.

---

## 1. Classification Definitions

| Classification | Meaning | Action for School Admin Web Portal |
|---|---|---|
| `SUPPORTED_NOW` | Fully implemented and verified in backend with active-context or legacy-compatibility support. | Web Portal can consume immediately. |
| `BACKEND_API_GAP` | Required for School Admin Web Portal functionality, but no customer-facing backend API currently exists. | Must be implemented in Backend Phase W2 / W6 before web module consumption. |
| `DEFERRED` | Out of scope for V1 School Admin Web Portal (e.g. Platform Owner Control Plane, subscriptions, external providers). | Excluded from V1 Web Portal scope. |

---

## 2. API Capability Matrix by Functional Domain

### 2.1 Authentication & Context Management

| Capability | Backend Endpoint | HTTP Method | Classification | Notes |
|---|---|---|---|---|
| User Login | `/api/v1/auth/login/` | `POST` | `SUPPORTED_NOW` | Returns JWT tokens (`access`, `refresh`), user profile, active context, `contexts_count`, `has_multiple_contexts`, and `default_membership_id`. |
| Token Refresh | `/api/v1/auth/refresh/` | `POST` | `SUPPORTED_NOW` | Single-flight refresh with replay detection. |
| Logout / Blacklist | `/api/v1/auth/logout/` | `POST` | `SUPPORTED_NOW` | Safely invalidates refresh token for the authenticated user. |
| Current User / Me | `/api/v1/auth/me/` | `GET` | `SUPPORTED_NOW` | Returns current user profile with active context and legacy projection. |
| List User Contexts | `/api/v1/auth/contexts/` | `GET` | `SUPPORTED_NOW` | Lists all school memberships with unread notification/conversation counts, `access_mode`, `is_default`, and `academic_year`. |
| Current Context | `/api/v1/auth/context/` | `GET` | `SUPPORTED_NOW` | Returns the currently active `SchoolMembership`. |
| Set Default Context | `/api/v1/auth/context/default/` | `POST` | `SUPPORTED_NOW` | Explicitly updates `is_default` and `last_used_at` with audit logging. |
| Context Header (`X-School-Membership-ID`) | All protected endpoints | Header | `SUPPORTED_NOW` | Resolves tenant scope. Returns 409 `context_required` if ambiguous. |
| Historical Context (Read-Only) | All protected endpoints | Header | `SUPPORTED_NOW` | Blocks mutations with 403; allows safe reads and personal read markers. |
| Unavailable Context Handling | All protected endpoints | Header | `SUPPORTED_NOW` | Blocks `suspended`, `ended`, or inactive schools with 403. |

---

### 2.2 School Admin Authorization & Role Guards

| Capability | Backend Endpoint | HTTP Method | Classification | Notes |
|---|---|---|---|---|
| School Admin Role Verification | Context resolution / Permissions | Internal | `SUPPORTED_NOW` | Validates `role === 'school_admin' || role === 'super_admin'`. |
| Multi-tenant School Scoping | QuerySet filtering / Permissions | Internal | `SUPPORTED_NOW` | Strict tenant isolation via `active_school`. Direct foreign IDs return 404. |
| School Profile & Settings Management | `/api/v1/school/settings/` (pending) | `GET`/`PUT` | `BACKEND_API_GAP` | School Admin needs customer-facing school profile/branding API (Scheduled for W2). |

---

### 2.3 Academic Master-Data CRUD

| Capability | Backend Endpoint | HTTP Method | Classification | Notes |
|---|---|---|---|---|
| Academic Years CRUD | `/api/v1/academic-years/` (pending) | `GET`/`POST`/`PUT`/`DELETE` | `BACKEND_API_GAP` | Only brief serializers and Django Admin currently exist. |
| Academic Terms CRUD | `/api/v1/academic-terms/` (pending) | `GET`/`POST`/`PUT`/`DELETE` | `BACKEND_API_GAP` | No customer-facing CRUD API currently exists. |
| Classrooms CRUD | `/api/v1/classrooms/` (pending) | `GET`/`POST`/`PUT`/`DELETE` | `BACKEND_API_GAP` | Read-only teacher class endpoint exists; admin CRUD is missing. |
| Sections CRUD | `/api/v1/sections/` (pending) | `GET`/`POST`/`PUT`/`DELETE` | `BACKEND_API_GAP` | No customer-facing CRUD API currently exists. |
| Subjects CRUD | `/api/v1/subjects/` (pending) | `GET`/`POST`/`PUT`/`DELETE` | `BACKEND_API_GAP` | Read-only teacher subject endpoint exists; admin CRUD is missing. |
| Class-Subject Mappings CRUD | `/api/v1/class-subjects/` (pending) | `GET`/`POST`/`PUT`/`DELETE` | `BACKEND_API_GAP` | No customer-facing CRUD API currently exists. |

---

### 2.4 People Management CRUD

| Capability | Backend Endpoint | HTTP Method | Classification | Notes |
|---|---|---|---|---|
| Student List & Search | `/api/v1/students/` | `GET` | `SUPPORTED_NOW` | Filters by search keyword, tenant-scoped. |
| Student Detail | `/api/v1/students/<pk>/` | `GET` | `SUPPORTED_NOW` | Read-only student profile. |
| Student Academic History | `/api/v1/students/<pk>/academic-history/` | `GET` | `SUPPORTED_NOW` | Historical enrollments list. |
| Student Create / Update / Delete | `/api/v1/students/` (pending) | `POST`/`PUT`/`DELETE` | `BACKEND_API_GAP` | Admin write operations needed (Scheduled for W2). |
| Student Enrollment Management | `/api/v1/student-enrollments/` (pending) | `GET`/`POST`/`PUT` | `BACKEND_API_GAP` | Admin enrollment creation and status updates needed. |
| Student Multi-School Transfer | `/api/v1/students/<pk>/transfer/` | `POST` | `SUPPORTED_NOW` | Super Admin atomic student transfer between schools. |
| Parent / Guardian CRUD | `/api/v1/parents/` (pending) | `GET`/`POST`/`PUT`/`DELETE` | `BACKEND_API_GAP` | Only `parents/me/children/` exists for parent role. |
| StudentGuardian Link Management | `/api/v1/student-guardians/` (pending) | `GET`/`POST`/`DELETE` | `BACKEND_API_GAP` | Admin linking/unlinking needed (Scheduled for W2). |
| Teacher CRUD | `/api/v1/teachers/` (pending) | `GET`/`POST`/`PUT`/`DELETE` | `BACKEND_API_GAP` | Only `teachers/me/*` exists for teacher self-read. |
| TeacherAssignment CRUD | `/api/v1/teacher-assignments/` (pending) | `GET`/`POST`/`PUT`/`DELETE` | `BACKEND_API_GAP` | Assignment options exist for timetable; admin CRUD needed. |

---

### 2.5 Timetable Administration

| Capability | Backend Endpoint | HTTP Method | Classification | Notes |
|---|---|---|---|---|
| Timetable Configuration | `/api/v1/timetable/config/` | `GET`/`PUT` | `SUPPORTED_NOW` | Working days, periods per day, period duration. |
| Period Management | `/api/v1/timetable/periods/` | `GET`/`POST`/`PUT`/`DELETE` | `SUPPORTED_NOW` | List, create, update, delete, and bulk periods. |
| Timetable Grid View | `/api/v1/timetable/grid/` | `GET` | `SUPPORTED_NOW` | Class-level and section-level schedule matrix. |
| Timetable Entries CRUD | `/api/v1/timetable/entries/` | `GET`/`POST`/`PUT`/`DELETE` | `SUPPORTED_NOW` | Single entry mutations with conflict checks. |
| Atomic Bulk Timetable Save | `/api/v1/timetable/bulk/` | `POST` | `SUPPORTED_NOW` | Final-state atomic upsert/clear with conflict validation. |
| Timetable Validation Preview | `/api/v1/timetable/validate/` | `POST` | `SUPPORTED_NOW` | Feasibility and conflict checking without persistence. |
| Copy Day / Week Schedule | `/api/v1/timetable/copy-day/`, `copy-week/` | `POST` | `SUPPORTED_NOW` | Replicates schedule across days/weeks. |
| Assignment Options for Slot | `/api/v1/timetable/assignment-options/` | `GET` | `SUPPORTED_NOW` | Returns available teacher assignments for given slot. |
| Teacher / Student Timetable | `/api/v1/timetable/today|week|current|next/` | `GET` | `SUPPORTED_NOW` | Role-based read views. |

---

### 2.6 Daily Attendance Administration

| Capability | Backend Endpoint | HTTP Method | Classification | Notes |
|---|---|---|---|---|
| Attendance List & Filters | `/api/v1/attendance/` | `GET` | `SUPPORTED_NOW` | Filter by date, classroom, section, student. |
| Attendance Record Creation | `/api/v1/attendance/` | `POST` | `SUPPORTED_NOW` | Create single attendance record. |
| Bulk Attendance Recording | `/api/v1/attendance/bulk/` | `POST` | `SUPPORTED_NOW` | Atomic bulk status recording for classroom/section. |
| Daily Attendance Report | `/api/v1/attendance/daily/` | `GET` | `SUPPORTED_NOW` | Aggregated daily metrics and status breakdowns. |
| Student Attendance Summary | `/api/v1/attendance/student/<id>/summary/` | `GET` | `SUPPORTED_NOW` | Summary statistics per student. |
| Class Attendance Summary | `/api/v1/attendance/class/<id>/summary/` | `GET` | `SUPPORTED_NOW` | Summary statistics per classroom. |

---

### 2.7 Homework Oversight

| Capability | Backend Endpoint | HTTP Method | Classification | Notes |
|---|---|---|---|---|
| Homework List & Oversight | `/api/v1/homework/` | `GET` | `SUPPORTED_NOW` | Filter by status, classroom, section, subject, teacher. |
| Homework Create / Edit / Delete | `/api/v1/homework/`, `/api/v1/homework/<pk>/` | `POST`/`PUT`/`PATCH`/`DELETE` | `SUPPORTED_NOW` | Full lifecycle management. |
| Publish / Close Homework | `/api/v1/homework/<pk>/publish/`, `close/` | `POST` | `SUPPORTED_NOW` | State transitions with atomic audits. |
| Bulk Publish / Close | `/api/v1/homework/bulk-publish/`, `bulk-close/` | `POST` | `SUPPORTED_NOW` | Atomic multi-homework operations. |
| Homework Dashboard & Summaries | `/api/v1/homework/dashboard/`, `summary/` | `GET` | `SUPPORTED_NOW` | Aggregated completion and submission statistics. |
| Submissions & Bulk Grading | `/api/v1/homework-submissions/` | `GET`/`POST` | `SUPPORTED_NOW` | Submission review and grading oversight. |

---

### 2.8 Exams & Results Administration

| Capability | Backend Endpoint | HTTP Method | Classification | Notes |
|---|---|---|---|---|
| Exam Types CRUD | `/api/v1/exam-types/`, `/api/v1/exam-types/<pk>/` | `GET`/`POST`/`PUT`/`DELETE` | `SUPPORTED_NOW` | Admin exam type definition. |
| Exams CRUD | `/api/v1/exams/`, `/api/v1/exams/<pk>/` | `GET`/`POST`/`PUT`/`DELETE` | `SUPPORTED_NOW` | Exam definitions and scheduling. |
| Exam Results Entry & Bulk | `/api/v1/exam-results/`, `exam-results/bulk/` | `GET`/`POST` | `SUPPORTED_NOW` | Grade entry and atomic bulk grading. |
| Result Approval Workflow | `/api/v1/exam-results/<pk>/approve/`, `reject/`, `reopen/` | `POST` | `SUPPORTED_NOW` | Strict admin workflow transitions. |
| Result Publication | `/api/v1/exams/<pk>/publish/`, `unpublish/`, `bulk-publish/` | `POST` | `SUPPORTED_NOW` | Atomic publication of approved results with audit logs. |
| Exam Result Audit Logs | `/api/v1/exam-results/<pk>/logs/` | `GET` | `SUPPORTED_NOW` | Full audit trail per result. |
| Result Reports & Transcripts | `/api/v1/exam-results/reports/*` | `GET` | `SUPPORTED_NOW` | Student transcripts, class/subject/exam summaries. |

---

### 2.9 Communications & Support

| Capability | Backend Endpoint | HTTP Method | Classification | Notes |
|---|---|---|---|---|
| Announcements CRUD & Lifecycle | `/api/v1/announcements/`, `publish/`, `close/`, `archive/` | `GET`/`POST`/`PUT`/`DELETE` | `SUPPORTED_NOW` | Full announcement lifecycle with role/class targeting. |
| Announcement Target Preview | `/api/v1/announcements/<pk>/target-preview/` | `GET` | `SUPPORTED_NOW` | Previews targeted recipients count and breakdown. |
| Announcement Attachments | `/api/v1/announcements/<pk>/attachments/` | `POST`/`DELETE` | `SUPPORTED_NOW` | Atomic attachment upload and removal. |
| School Inbox (Support Tickets) | `/api/v1/school-inbox/`, `assign/`, `status/`, `reply/` | `GET`/`POST` | `SUPPORTED_NOW` | Admin ticket triage, assignment, status and replies. |
| Conversations & Messages | `/api/v1/conversations/`, `messages/`, `read/` | `GET`/`POST` | `SUPPORTED_NOW` | Pairwise authorized conversations with attachments. |
| Notifications & Badges | `/api/v1/notifications/`, `/api/v1/communication/badges/` | `GET`/`POST` | `SUPPORTED_NOW` | Membership-scoped notification list, read marks, badges. |
| Teacher Broadcast | `/api/v1/notifications/broadcast/` | `POST` | `SUPPORTED_NOW` | Assignment-scoped notification dispatch to students/parents. |

---

### 2.10 Dashboard Aggregation

| Capability | Backend Endpoint | HTTP Method | Classification | Notes |
|---|---|---|---|---|
| Unified School Admin Overview KPI | `/api/v1/dashboard/admin/` (pending) | `GET` | `BACKEND_API_GAP` | Single composite operational summary (students, teachers, today's attendance, pending approvals, inbox tickets, timetable health) needed for Phase W3. |

---

### 2.11 Data Import & Export Center

| Capability | Backend Endpoint | HTTP Method | Classification | Notes |
|---|---|---|---|---|
| Excel Import Job Pipeline | `/api/v1/imports/*` (pending) | `POST` | `BACKEND_API_GAP` | Multi-step pipeline (`upload → validate → preview → commit`) for academic & people data (Phase W6). |
| Excel Tenant Export Center | `/api/v1/exports/*` (pending) | `GET`/`POST` | `BACKEND_API_GAP` | Scoped XLSX exports for students, attendance, results, timetable, and assignments (Phase W6). |

---

### 2.12 Platform Control Plane & Deferred Features

| Capability | Backend Endpoint | Classification | Notes |
|---|---|---|---|
| Platform Owner Control Plane | `/api/platform/v1/*` | `DEFERRED` | Out of scope for School Admin Portal. |
| SaaS Subscriptions & Billing | N/A | `DEFERRED` | Future platform tier. |
| Cross-School Teacher Conflict Warning | N/A | `DEFERRED` | Privacy-safe multi-school warning planned post-V1. |
| Timetable Bell-Time Versioning & Exceptions | N/A | `DEFERRED` | Future timetable enhancements. |

---

## 3. Summary Statistics

- **Total Capabilities Assessed:** 44
- **`SUPPORTED_NOW`:** 28 (63.6%)
- **`BACKEND_API_GAP`:** 12 (27.3%)
- **`DEFERRED`:** 4 (9.1%)
