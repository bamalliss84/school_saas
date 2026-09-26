# Mobile Status

## Student App

- Student Mobile V1: **CLOSED**.
- Student Results filtering and presentation fixes: **Integrated**.
- Result visibility preserves the approved/published semantics enforced by the current implementation.

## Teacher App

| Milestone | Status |
| --- | --- |
| M2.1 — Shell & Context | CLOSED |
| M2.2 — Teacher Timetable | CLOSED — Runtime Accepted |
| M2.3 — Teacher Assignments + Lesson Roster | CLOSED — Runtime Accepted |
| M2.4 — Teacher Attendance | CLOSED — Runtime Accepted |
| M2.5 — Teacher Homework | CLOSED — Runtime Accepted |
| M2.6 — Teacher Exams & Results | CLOSED — Runtime Accepted |
| M2.7 — Teacher Communications | CLOSED — Runtime Accepted |

This is the current milestone numbering. The former numbering that separated Submissions and shifted Exams/Results and Communications is obsolete.

`TeacherShell` opens `TeacherWorkCenterScreen`, which includes `TeacherHomeworkScreen` and Exams/Results.

Teacher communications support notifications, the announcement lifecycle, and Teacher → Student conversations. Teacher → Parent new-conversation creation is **Deferred** until a safe teacher-scoped parent/guardian recipient-discovery contract exists; raw membership IDs are not an acceptable solution.

## Release 1.0 UI/UX

A formal Mobile + Web UI/UX review/redesign remains **Planned** after functional stabilization. It must preserve approved business rules and API contracts.
