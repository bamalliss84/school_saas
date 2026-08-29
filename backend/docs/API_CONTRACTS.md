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
      "created_at": "2026-08-29T10:00:00Z"
    }
  ]
}
```
