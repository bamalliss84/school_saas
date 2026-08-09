# Sprint 4.7 — Timetable & Daily Schedule

## Architecture

`TeacherAssignment` answers **who teaches what to whom**. `TimetableEntry` references that assignment and answers **when and where**. Teacher, classroom, section and subject are not duplicated.

The canonical authorization sources are `request.active_membership`, `request.active_school`, `request.active_role`, and `request.active_academic_year`. New timetable code does not authorize from legacy User fields. Active contexts are writable only for School Admin/Super Admin; historical contexts are read-only for every role.

## Models

- `SchoolTimetableConfig`: configurable unique working weekdays per school/year.
- `SchoolPeriod`: ordered lesson/break time definitions; unique sequence and non-overlapping valid times.
- `TimetableEntry`: weekly weekday+lesson period+TeacherAssignment with optional room and validity dates.

Migration `0024_timetable_daily_schedule` is additive. It does not infer schedule rows from `weekly_periods`; existing schools start empty.

Same-school overlapping validity conflicts block the same Teacher and the same Classroom+Section. Break periods are timeline rows, never teaching entries. Cross-school conflict warnings and calendar exceptions are deferred to avoid tenant disclosure and architecture inflation.

## SCHOOL TIMETABLE ADMIN UX

1. Select the academic year through context/year selection.
2. Select Classroom and Section.
3. Load one Grid response containing days, periods and entries.
4. Tap a cell.
5. Load valid TeacherAssignment options and choose “Teacher — Subject”.
6. Send one atomic bulk save, optionally previewed with validate-only.

There is no long wizard and no repeated School/Teacher/Subject/Class/Section selection per cell. Copy day/week and clear operations reduce manual entry. The bulk contract can support a future import adapter, but Sprint 4.7 does not implement Excel import.

## Read contract

Teacher, Student, linked Parent, School Admin and context-scoped Super Admin can use Today/Week/Current/Next. Student scope comes from the enrollment in the selected school/year. Parent must name a linked child. Current is today-only; Next searches across at most 14 days. Status is derived with timezone-aware Django utilities.

Attendance remains authorized by Active Context+TeacherAssignment. Timetable only exposes query-efficient attendance shortcut metadata; missing timetable data never disables existing Attendance APIs.

## Deferred

School calendar/holidays/exceptions, cross-school privacy-safe teacher warning, room management, timetable Excel import, automatic templates and Flutter.

## Sprint 4.7.1 Hardening

- Attendance shortcut state is daily per Classroom+Section: `not_recorded`, `partial`, or `recorded`, with recorded and expected student counts. It is not period attendance.
- `can_take_attendance` is true only for the owning Teacher in a writable current context on today's current/upcoming lesson; Student, Parent, Admin and historical contexts receive false.
- A working day with existing entries cannot be removed, and a used lesson period cannot become a break or be deleted.
- Bulk and copy preview/save project the same final state: logical clears first, then upserts, then one final conflict validation and atomic write.
- Changing period times affects every timetable date using that period. Bell schedule versioning remains deferred.
