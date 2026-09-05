# School SaaS — Shared Backend API Contracts

## Attendance Management APIs

### 1. Bulk Attendance Mutation (`POST /api/v1/attendance/bulk/`)

Creates or updates daily attendance records in bulk for a specific teacher assignment and date within the active academic context.

> **Important Architecture Rule:**  
> **Academic Term resolution for Attendance mutations is server-owned.**  
> Clients (Web, Mobile, future clients) must **NOT** infer or guess `AcademicTerm` locally.

#### Request Headers
- `Authorization: Bearer <access_token>`
- `X-School-Id: <active_school_id>`
- `X-Academic-Year-Id: <active_academic_year_id>` (optional if default/active context selected)

#### Canonical Request Payload (Modern Web / Mobile)
```json
{
  "teacher_assignment_id": 123,
  "attendance_date": "2026-08-29",
  "students": [
    {
      "student_enrollment_id": 789,
      "status": "present",
      "note": ""
    },
    {
      "student_enrollment_id": 790,
      "status": "absent",
      "note": "Unexcused"
    }
  ]
}
```

#### Field Specifications
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `teacher_assignment_id` | Integer | Yes | The authorized `TeacherAssignment` ID for the active school/year. |
| `attendance_date` | Date (YYYY-MM-DD) | Yes | The date of attendance to record. |
| `academic_term_id` | Integer | **Optional** | Backward compatibility pointer. If provided, server validates that it exactly matches the server-resolved term. |
| `students` | Array of Objects | Yes | Non-empty list of student attendance entries. Duplicate enrollment IDs are rejected. |
| `students[].student_enrollment_id` | Integer | Yes | The student's current active `StudentEnrollment` ID in the assigned class and section. |
| `students[].status` | String | Yes | Attendance status: `present`, `absent`, `late`, `excused`. |
| `students[].note` | String | No | Optional notes/reason. |

#### Server-Side Academic Term Resolution
The Backend resolves the applicable `AcademicTerm` using:
- `school = request.active_school`
- `academic_year = request.active_academic_year`
- `start_date <= attendance_date <= end_date`
- TeacherAssignment academic context

**Resolution Rules:**
1. **Exactly One Term Matches:** The resolved term is automatically linked to all created/updated attendance records.
2. **Zero Terms Match:** Returns HTTP 400 Bad Request with a clear validation error indicating no academic term covers the specified date.
3. **Multiple Terms Match (Ambiguous Configuration):** Returns HTTP 400 Bad Request indicating ambiguous configuration. The system never arbitrarily picks a term.
4. **Backward Compatibility:** If an older client supplies `academic_term_id`, the server resolves the canonical term anyway and validates that the supplied ID matches the resolved term. If mismatched or belonging to another school/year, it returns HTTP 400.

#### Response Contract (HTTP 200 OK)
```json
{
  "success": true,
  "created": 2,
  "updated": 0,
  "total": 2,
  "academic_term": {
    "id": 456,
    "name": "الفصل الدراسي الأول"
  },
  "records": [
    {
      "id": 1001,
      "student_enrollment": 789,
      "student": {
        "id": 501,
        "student_code": "STU-001",
        "full_name": "طالب تجريبي أول"
      },
      "teacher_assignment": 123,
      "academic_term": 456,
      "academic_term_detail": {
        "id": 456,
        "name": "الفصل الدراسي الأول",
        "term_type": "term_1",
        "start_date": "2026-08-20",
        "end_date": "2026-12-31"
      },
      "attendance_date": "2026-08-29",
      "status": "present",
      "note": "",

## Homework & Evaluation APIs (Teacher Work Center)

### 1. Homework Creation & Academic Term Resolution (`POST /api/v1/homework/`)

Creates a new homework draft within the authorized teacher's assignment scope.

> **Important Architecture Rule:**
> **Academic Term resolution for Homework creation is server-owned.**
> `academic_term` is optional in the request payload. The server derives the canonical term from the active context and the homework's `due_date`.

#### Request Headers
- `Authorization: Bearer <access_token>`
- `X-School-Membership-ID: <active_membership_id>` (or default active context)

#### Request Payload
```json
{
  "teacher_assignment": 123,
  "title": "فروض الجبر والتحليل",
  "description": "حل التمارين من 1 إلى 5 صفحة 45",
  "due_date": "2026-03-20T18:00:00Z",
  "max_grade": "20.00",
  "submission_type": "both",
  "academic_term": null
}
```

#### Field Specifications
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `teacher_assignment` | Integer | Yes | Authorized `TeacherAssignment` ID belonging to active teacher/school. |
| `title` | String | Yes | Homework title. |
| `description` | String | No | Homework instructions and details. |
| `due_date` | DateTime | Yes | Due date/time for submission. Used as the anchor date for term resolution. |
| `max_grade` | Decimal | No | Maximum grade (default `100.00`). |
| `submission_type` | String | No | `file`, `text`, or `both` (default `both`). |
| `academic_term` | Integer | **Optional** | Backward compatibility only. If provided, server validates that it matches the server-resolved term exactly. |

#### Server-Side Academic Term Resolution Rules
1. **Inputs:** `school = request.active_school`, `academic_year = request.active_academic_year`, and `due_date.date()`.
2. **Exactly One Term Matches:** Server links the resolved `AcademicTerm` to the homework.
3. **Zero Matching Terms:** Returns HTTP 400 Bad Request with a clear validation error (`No academic term covers the specified homework due date.`).
4. **Multiple Matching Terms:** Returns HTTP 400 Bad Request indicating ambiguous configuration.
5. **Client-Supplied Term Validation:** If client provides `academic_term`, server validates that `supplied_term.pk == resolved_term.pk`. Mismatches are rejected with HTTP 400.

---

### 2. Homework Student Status / Work Center Roster (`GET /api/v1/homework/<id>/student-status/`)

Authoritative roster view for the Teacher Work Center (**المهام والتقييم**). Returns all target students enrolled in the assigned classroom/section, projecting each student's submission status without duplicating database records.

#### Request Headers
- `Authorization: Bearer <access_token>`
- `X-School-Membership-ID: <active_membership_id>`

#### Query Parameters
- `status`: Filter by projected status: `not_started`, `draft`, `submitted`, `graded`, `returned`.
- `search`: Case-insensitive search on student full name or student code.

#### Response Contract (HTTP 200 OK)
```json
{
  "homework_id": 42,
  "total_students": 30,
  "submitted_count": 25,
  "graded_count": 20,
  "draft_count": 2,
  "not_started_count": 3,
  "pending_grading_count": 5,
  "students": [
    {
      "student_enrollment_id": 101,
      "student_id": 501,
      "student_code": "STU-1001",
      "student_name": "طارق المنصور",
      "student_gender": "male",
      "homework_id": 42,
      "submission_id": 201,
      "status": "graded",
      "submitted_at": "2026-03-18T14:30:00Z",
      "is_late": false,
      "grade": "18.50",
      "max_grade": "20.00",
      "teacher_note": "عمل ممتاز",
      "can_grade": false,
      "can_return": true
    },
    {
      "student_enrollment_id": 102,
      "student_id": 502,
      "student_code": "STU-1002",
      "student_name": "أحمد خليل",
      "student_gender": "male",
      "homework_id": 42,
      "submission_id": 202,
      "status": "submitted",
      "submitted_at": "2026-03-19T10:00:00Z",
      "is_late": false,
      "grade": null,
      "max_grade": "20.00",
      "teacher_note": null,
      "can_grade": true,
      "can_return": true
    },
    {
      "student_enrollment_id": 103,
      "student_id": 503,
      "student_code": "STU-1003",
      "student_name": "سامي يوسف",
      "student_gender": "male",
      "homework_id": 42,
      "submission_id": null,
      "status": "not_started",
      "submitted_at": null,
      "is_late": false,
      "grade": null,
      "max_grade": "20.00",
      "teacher_note": null,
      "can_grade": false,
      "can_return": false
    }
  ]
}
```

---

### 3. Supported Teacher Homework Filters (`GET /api/v1/homework/` and `GET /api/v1/teachers/me/homework/`)

| Query Parameter | Type | Description |
| :--- | :--- | :--- |
| `status` | String | Homework status: `draft`, `published`, `closed`. |
| `academic_year_id` | Integer | Filter by academic year ID. |
| `academic_term_id` | Integer | Filter by academic term ID. |
| `teacher_assignment_id` | Integer | Filter by teacher assignment ID. |
| `classroom_id` | Integer | Filter by classroom ID. |
| `section_id` | Integer | Filter by section ID. |
| `subject_id` | Integer | Filter by subject ID. |
| `search` | String | Search across homework `title` and `description`. |
| `publish_from` / `publish_to` | DateTime | Filter by `published_at` timestamp range. |
| `due_from` / `due_to` | DateTime | Filter by `due_date` timestamp range. |
| `overdue` | Boolean | True filters for past `due_date`; False for upcoming. |
| `has_submission` | Boolean | True filters homework with at least one submission. |
| `submission_status` | String | Filter homework having submissions in `draft`, `submitted`, or `graded`. |
| `graded` | Boolean | True filters homework with graded submissions; False excludes graded. |
| `pending_grading` | Boolean | True filters homework having submissions in `submitted` status waiting for grading. |
| `ordering` | String | Sort order (e.g. `-created_at`, `due_date`, `-due_date`, `title`). |
