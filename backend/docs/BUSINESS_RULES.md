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
