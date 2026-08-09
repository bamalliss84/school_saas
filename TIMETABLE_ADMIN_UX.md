# Timetable Admin UX Contract

## Primary workflow

Choose Academic Year, Classroom and Section once. `GET timetable/grid/` returns working days, display periods (including breaks), and entries. A cell picker calls `assignment-options/`, returning only compatible assignments as “Teacher — Subject”. One `timetable/bulk/` request saves changed cells.

Required states: empty period setup, empty schedule, loading, dirty grid, valid preview, cell conflicts, atomic save success, unavailable foreign/stale object, and read-only historical context.

## Operations

- Upsert requires assignment, lesson period and weekday; room/validity are optional.
- Clear sends the entry ID with `action=clear`; replace uses upsert with its ID.
- Validate sends changed cells to `/validate/` and never writes.
- Copy Day/Week maps subjects to compatible target assignments; missing assignments produce validation, never incorrect rows.
- Clear target is explicit; there is no hidden destructive overwrite.

## Period setup and guardrails

Working days and periods are configured once per school/year. Period bulk setup is atomic. The backend imposes no default times and does not derive schedule from `weekly_periods`. Used periods cannot be deleted.

Teacher/Student/Parent never see edit controls. Historical mode hides all mutation. No cross-school conflict detail, free teacher selection, repeated seven-dropdown cell form, Excel import, room module, calendar exception editor or Flutter implementation exists in Sprint 4.7.

## Sprint 4.7.1 Hardening

- Working days containing entries cannot be removed until those entries are cleared.
- Used lesson periods cannot become breaks or be deleted. Time edits affect all timetable dates using the period; bell-time versioning is deferred.
- Grid bulk operations support final-state move/swap/replace semantics. Preview and save use identical clear-first projection, including copy day/week with `clear_target`.
- Attendance badges describe daily class completion, not lesson attendance. Only the eligible owning Teacher receives an enabled attendance shortcut.
