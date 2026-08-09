# Timetable API Contract

Canonical prefix: `/api/v1/`; `/api/` remains the existing compatibility alias. JWT school requests send `X-School-Membership-ID`. Foreign scoped identifiers return 404 where practical.

## Administration

| Method/path | Purpose |
|---|---|
| GET/PUT `timetable/config/` | working days; PUT School Admin/Super Admin only |
| GET/POST `timetable/periods/` | period setup |
| GET/PUT/PATCH/DELETE `timetable/periods/{id}/` | period maintenance; used periods are protected |
| POST `timetable/periods/bulk/` | atomic setup replacement while unused |
| GET/POST `timetable/entries/` | filtered paginated entries/create |
| GET/PUT/DELETE `timetable/entries/{id}/` | scoped entry operations |
| GET `timetable/grid/` | one bounded class/section Grid: days, periods, entries |
| POST `timetable/bulk/` | atomic upsert/clear; optional validate_only |
| POST `timetable/validate/` | preview without writes |
| POST `timetable/copy-day/`, `copy-week/` | compatible subject-assignment copy |
| GET `timetable/assignment-options/` | current assignments for class/section |

Conflict errors use the standard 400 envelope and grid-ready objects with `index`, `code`, `weekday`, `period_id`, `teacher_assignment_id`, and `message`. Codes include `exact_duplicate`, `teacher_conflict`, `class_section_conflict`, and `invalid_cell`. Bulk input is all-or-nothing.

## Role schedule

| Method/path | Contract |
|---|---|
| GET `timetable/today/` | date, weekday, current/next today, entries, periods |
| GET `timetable/week/` | seven bounded day objects |
| GET `timetable/current/` | current lesson today only or null |
| GET `timetable/next/` | next lesson across up to 14 days or null |

Teacher is restricted to owned assignments. Student uses the selected-context enrollment class/section. Parent supplies a guardian-linked `student_id`. Admin may filter by teacher/class/section. Super Admin remains tenant-context scoped.

Entries include Teacher/Subject/Classroom/Section, period, room, validity, derived `finished/current/upcoming`, and attendance shortcut metadata. Breaks appear in `periods`, never as lesson entries.

Query serializers validate date, weekday and scoped IDs. Grid/Today/Week are bounded and unpaginated; entry list uses standard pagination. Historical GET is supported in role scope; all historical timetable writes return 403. Existing Attendance/Homework/Exam/Messaging contracts are unchanged.

## Sprint 4.7.1 Hardening

Timeline attendance metadata is daily Classroom+Section state: `attendance_status` (`not_recorded`, `partial`, `recorded`), `attendance_count`, and additive `attendance_expected_count`. It never represents attendance for an individual period. `can_take_attendance` is role/context/date/assignment safe and defaults false outside the owning Teacher's writable current context.

Config rejects removing used weekdays with structured 400 validation. Used lesson periods cannot become breaks and protected deletion returns controlled 400. Bulk, validate, copy-day and copy-week all validate the projected final state; `clear_target=true` is simulated during preview without database mutation, so preview and save feasibility match.
