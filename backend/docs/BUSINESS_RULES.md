# School SaaS — Backend Business Rules

## Attendance & Academic Term Domain Rules

### 1. Server-Owned Academic Term Resolution
- **Rule Statement:** **Academic Term resolution for Attendance mutations is server-owned.**
- **Rationale:** Neither Web nor Mobile clients possess complete global knowledge of term boundaries or administrative calendar changes.
- **Resolution Constraints:**
  - The server identifies the unique active `AcademicTerm` where `school_id == assignment.school_id`, `academic_year_id == assignment.academic_year_id`, and `start_date <= attendance_date <= end_date`.
  - If zero terms match the attendance date, the mutation is rejected with HTTP 400.
  - If multiple terms overlap and match the attendance date, the configuration is considered ambiguous and rejected with HTTP 400.
  - Clients must never attempt to infer or calculate the term locally.

### 2. Multi-Tenant Active Context Enforcement
- Canonical context source: `request.active_membership`, `request.active_school`, `request.active_role`, `request.active_academic_year`.
- Mutations are strictly prohibited in historical contexts (`is_historical == True` or `access_mode == 'read_only'`). Any write attempt returns HTTP 403 Forbidden.
- All relationships (`TeacherAssignment`, `StudentEnrollment`, `AcademicTerm`) must belong to the active school and active academic year.

### 3. Attendance Mutation Safety & Idempotency
- **Atomic Bulk Transaction:** Bulk attendance mutations execute within a single database transaction. If any student or constraint fails, the entire batch rolls back.
- **Upsert Semantics:** If attendance already exists for `(student_enrollment, attendance_date)`, the existing record is updated with new status and note; otherwise, a new record is created.
- **Duplicate Prevention:** Submitting duplicate `student_enrollment_id` entries within the same request payload is rejected with HTTP 400.
- **Date Bounds Validation:** The `attendance_date` must fall within both the `TeacherAssignment` validity dates (`start_date`, `end_date`) and the resolved `AcademicTerm` date bounds (`start_date`, `end_date`).

## Homework & Evaluation Domain Rules (Sprint M2.5)

### 1. Server-Owned Homework Academic Term Resolution
- **Rule Statement:** **Academic Term resolution for Homework creation is server-owned.**
- **Inputs:** Active school context (`request.active_school`), active academic year (`request.active_academic_year`), authorized `TeacherAssignment`, and homework `due_date`.
- **Resolution Constraints:**
  - The server queries `AcademicTerm` for matching `school`, `academic_year`, where `start_date <= due_date.date() <= end_date`.
  - **Zero Matches:** Rejects creation with HTTP 400 (`No academic term covers the specified homework due date.`).
  - **Multiple Matches (Ambiguous):** Rejects creation with HTTP 400 (`Multiple academic terms cover the specified homework due date; configuration is ambiguous.`).
  - **Client-Supplied Term Compatibility:** If an older client supplies `academic_term`, the server validates that it equals the server-resolved canonical term. Any mismatch returns HTTP 400.
  - **Client Guideline:** Clients should omit `academic_term` during homework creation and let the server resolve it deterministically from `due_date`.

### 2. Active Context & Role Authorization
- **Canonical Authority:** Authorization across all homework and submission endpoints is derived strictly from `request.active_role`, `request.active_membership`, `request.active_school`, and `request.active_academic_year`.
- **Legacy Compatibility:** `request.user.role` and `request.user.school` are fallback pointers for legacy/unmigrated code; all request paths authorize from the active membership context.
- **Multi-Role Behavior:** Users possessing multiple memberships (e.g. School Admin in School A and Teacher in School B) act solely according to the currently active context selected in headers/tokens. Cross-school access is strictly isolated (returns HTTP 404).

### 3. Historical Context Write Protection
- **Rule Statement:** **Historical academic context is strictly read-only for all Homework and Submission mutations.**
- **Enforced Endpoints:**
  - Homework: create (`POST /api/v1/homework/`), update (`PUT`/`PATCH`), delete (`DELETE`), publish (`POST /publish/`), close (`POST /close/`), bulk publish, bulk close.
  - Attachments: upload (`POST /attachments/`), delete (`DELETE /attachments/<id>/`).
  - Submissions: create draft, patch draft, final submit, teacher grade (`POST /grade/`), teacher bulk grade (`POST /bulk-grade/`), teacher return (`POST /return/`).
- **Violation Response:** All write attempts in historical context immediately return HTTP 403 Forbidden (`Historical school context is read-only.`).
- **Read Access:** Historical contexts retain read-only GET access where authorized (including homework details, submissions lists, and student-status roster).

### 4. `publish_at` Runtime Semantics
- **Audit Finding:** There is **NO automatic background worker, cron job, or Celery scheduler** that automatically transitions homework from `draft` to `published` when `publish_at` timestamp is reached.
- **Domain Contract:** `publish_at` is a validated metadata field (`due_date >= publish_at`). Publication is strictly triggered by an explicit API call to `POST /api/v1/homework/<id>/publish/` (or `bulk-publish/`).
- **Client Impact:** Mobile and Web clients must not represent `publish_at` as an automatic scheduled release trigger until a dedicated backend scheduler subsystem is formally architected and deployed.

### 5. Work Center Student Status Projection
- **Authoritative Scope:** The student-status roster (`GET /api/v1/homework/<id>/student-status/`) projects the complete enrolled student body from the homework's `TeacherAssignment` (matching school, academic year, classroom, and section).
- **Domain Projection:** Students without submission records are projected with status `not_started`, `submission_id = null`, `can_grade = false`, `can_return = false`.
- **Database Safety:** No dummy or fake `HomeworkSubmission` rows are inserted into the database for non-submitting students.
- **Tenant Isolation:** Students from other sections, classrooms, or schools are strictly excluded.
