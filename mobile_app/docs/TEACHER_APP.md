# Teacher App

## Role-Based Visual System

- The Teacher role accent is professional blue.
- The future Student role accent is green.
- The future Parent role accent is purple.
- Roles share one structural visual language: compact Arabic typography, light surfaces, rounded cards, restrained borders and shadows, and consistent spacing.
- Primary modules use Bottom Navigation as their canonical entry point. Home must avoid duplicate navigation and repeated generic actions.
- Teacher Home prioritizes the active school and academic context, the current lesson, the next lesson, and real attention items over menu-style shortcut grids.
- Teacher screens use the application `TextTheme` and existing Arabic font preference rather than a role-specific font dependency.

## M2.2 — Teacher Timetable

**Status:** CLOSED — Runtime Accepted.

### Endpoints

- `GET timetable/today/`
- `GET timetable/week/`
- `GET timetable/current/`
- `GET timetable/next/`

### Active Context

The Teacher Timetable uses `X-School-Membership-ID` through the existing `ApiClient`. State and cache data are isolated by user, membership, and academic year.

### Timetable Fields

The implementation uses these timetable response fields:

- `date`
- `weekday`
- `entries`
- `current_entry`
- `next_entry`
- `subject`
- `classroom`
- `section`
- `period_detail`
- `room_or_location`
- `status`

Period data uses:

- `name`
- `sequence`
- `start_time`
- `end_time`
- `kind`
- `is_active`

### Today UX

The Today view provides an operational summary, the current lesson, the next lesson, and a chronological timeline. It displays real breaks and only server-supported empty teaching periods; it does not fabricate empty periods.

### Week UX

The Week view uses a horizontal day selector built only from days returned by the backend.

### Time Semantics

Current, upcoming, and completed states are calculated from the actual local `DateTime`. The countdown is dynamic, with no periodic timer. Open Lesson appears only during an actual current lesson.

### Historical Context

Historical timetable contexts show a read-only banner. They do not show live urgency or a countdown, and do not expose the Open Lesson action.

### Cache and Offline Behavior

M2.2 reuses the existing timetable cache infrastructure. Today, week, current, and next responses use separate cache keys. Loading is cache-first followed by refresh, with cache fallback only for eligible connectivity errors. No new cache architecture was introduced.

### Student Isolation

The Teacher implementation does not reuse Student timetable screens, controllers, or models.

### API and Schema Impact

M2.2 makes no Backend, API, schema, or migration changes. No API gap was found for M2.2.

## M2.3 — Teacher Assignments and Lesson Roster

**Status:** CLOSED — Runtime Accepted.

### Endpoints

- `GET teachers/me/assignments/`
- `GET teachers/me/assignments/<assignment_id>/students/?date=YYYY-MM-DD`

The related `classes`, `subjects`, and union `students` contracts were inspected but are not needed by the assignment-first M2.3 information architecture.

### Assignment and Roster Semantics

Each card represents one real `TeacherAssignment`; assignments are not merged by subject, classroom, or section. Opening a card loads its assignment-specific roster, which is the canonical source for that group. The roster displays the returned subject, classroom, section, date, total student count, recorded attendance count, and roster students.

### Active Context and Historical Behavior

Requests use the existing `X-School-Membership-ID` behavior in `ApiClient`. Providers are isolated by local user, membership, and academic year, with the assignment ID included in roster requests. Changing context therefore creates a distinct provider scope and clears the selected assignment. Historical contexts remain visibly read-only.

### Attendance Boundary

Existing date-scoped attendance status and note are displayed read-only only when returned by the roster endpoint. M2.3 does not mark attendance, change statuses, edit notes, or send attendance mutations. Attendance mutation belongs to M2.4.

### Search and Offline Decision

Roster search is local over the already-loaded student name and student code, with no request per keystroke. M2.3 remains network-read-only because the existing local database has timetable-specific caching but no generic assignment/roster cache; no second cache architecture or offline write queue was introduced.

### API Gaps

No API gap blocks the assignment and roster foundation. There is no dedicated authorized teacher-facing full student-detail contract in M2.3, so the UI intentionally exposes only roster-safe fields and does not open a student profile.
