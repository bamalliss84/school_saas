# Sprint 4.7 Timetable Acceptance Report

## 1. Baseline

`06c5e08 Sprint 4.6: add demo data and end-to-end backend acceptance`; Sprint 4.6 baseline was 590 tests. Pre-existing untracked `BACKEND_UX_CONTRACT_*` files were preserved and not modified.

## 2. Architecture

`TeacherAssignment` remains WHO/WHAT/WHOM. Timetable models add WHEN/WHERE and all new authorization uses `request.active_*` only.

## 3. Models

`SchoolTimetableConfig`, `SchoolPeriod`, and `TimetableEntry`; no duplicated teacher/classroom/section/subject fields and no room subsystem.

## 4. Migration

Additive `0024_timetable_daily_schedule`; migrations 0001–0023 were not edited. No data migration from `weekly_periods`.

## 5. Constraints

Unique period sequence per school/year, start<end check, one config per year, validity date order and query indexes. Used period/assignment references are PROTECT.

## 6. Conflict algorithm

Service checks overlapping open-ended/date ranges for exact duplicate, same teacher and same classroom+section at weekday+period. Structured cell errors are atomic.

## 7. Multi-school behavior

Selected membership scopes every ID/query. Same-school conflicts are hard failures. Cross-school warning was deliberately deferred to avoid tenant disclosure and multi-school blocking.

## 8. Historical behavior

Role-scoped reads use the enrollment/year in the selected historical context. Authentication rejects all timetable writes with 403.

## 9. Period setup

Configurable working days and list/create/detail/update/delete/bulk period endpoints. Breaks are display periods and cannot own teaching entries.

## 10. Admin Grid

One GET returns days, periods and entries for classroom+section; no per-cell fan-out.

## 11. Bulk save

Atomic upsert/replace/clear with complete prevalidation, duplicate ID rejection, rollback on conflict and foreign ID 404.

## 12. Validation preview

`/timetable/validate/` forces validate-only and does not write. Bulk also accepts `validate_only`.

## 13. Copy day/week

Atomic copy maps target assignments by subject; incompatible target assignment returns validation. Explicit clear target only.

## 14. Assignment options

Returns only current context/year/classroom/section assignments as “Teacher — Subject”.

## 15. Teacher today

Returns date/weekday/current/next-today/entries/periods with derived status and attendance shortcut metadata.

## 16. Teacher week

Returns seven bounded days; each entry remains selected-membership assignment scoped.

## 17. Current lesson

Today only: start_time ≤ timezone-aware local now < end_time; break is never current.

## 18. Next lesson

Searches upcoming teaching entries across up to 14 days and returns null when none. It differs intentionally from Today's `next_entry`, which is same-day only.

## 19. Student schedule

Uses selected school/year enrollment classroom+section; no peer/class leakage and no writes.

## 20. Parent child schedule

Requires guardian-linked `student_id`; unrelated child is 404 and school contexts never mix.

## 21. Attendance integration

Timetable does not alter Attendance authorization. Today aggregates recorded attendance in one query and provides `attendance_status/count/can_take_attendance`.

## 22. Demo Seeder

Creates two school configs, current periods/entries, independent multi-school teacher schedules, and a historical School A timetable. Reset and repeat remain scoped/idempotent.

## 23. API E2E

JWT/context tests exercise Teacher A/B, deterministic Current/Next, Student, Parent and Admin Grid/Bulk/Validate/Copy/CRUD through REST.

## 24. Cross-school IDOR

Foreign entry and period IDs return 404; context switching yields disjoint entry IDs; unrelated parent child returns 404.

## 25. Performance/query counts

Select-related entry graph and aggregate attendance avoid N+1. Teacher Today is locked by `assertNumQueries(7)` including authentication/context queries. Grid/Today/Week are bounded and unpaginated; entry list is paginated.

## 26. Tests count

Final full command: 604/604 PASS in 538.388s. The subsequently added query-budget test passed independently, so the current suite contains 605 passing tests (15 Sprint 4.7 tests; 590 baseline retained).

## 27. Coverage

Combined full-suite plus final CRUD/Copy tests: `10785 statements / 800 missing / 93%` — PASS.

## 28. Ruff

`All checks passed!` for `backend/core` and `backend/config`.

## 29. Django check

`System check identified no issues (0 silenced)`.

## 30. Deploy warnings

Only the accepted development warnings: W004 HSTS, W008 SSL redirect, W009 development secret.

## 31. Migrations

0024 applied; `makemigrations --check --dry-run`: No changes detected; `migrate`: no pending migrations.

## 32. OpenAPI

Official `spectacular --validate`: zero errors and zero warnings after adding explicit APIView serializers and removing duplicate enum naming.

## 33. Live HTTP

Real Demo DB: login/contexts, multi-school Teacher Today/Week/Current/Next, Student Today, Parent child Week and Admin Grid succeeded. Both teacher memberships returned only one own-school Sunday entry and seven week days.

## 34. runserver count

Temporary `--noreload` server PID was stopped; `RUNSERVER_COUNT=0`.

## 35. Files added

Migration 0024; timetable selectors/serializers/views/service; three test files/sections (two new files); Sprint/API/Admin UX documents; this report.

## 36. Files modified

Models, API routing, Admin, Demo Seeder, AGENTS, README, Roadmap and Project Context. Existing domain APIs were not changed.

## 37. Bugs discovered

Initial live smoke script used context DTO `id` instead of `membership_id`, correctly receiving 409. Initial OpenAPI pass reported missing APIView serializer metadata and duplicate enum naming. Initial coverage was 92%. Query budget was measured with a deliberately zero expected count.

## 38. Bugs fixed

Live script used `membership_id`; schema metadata/enums were corrected to 0/0; CRUD/Config/Copy tests raised behavioral coverage to 93%; query budget was fixed at measured 7. No production regression bug was found.

## 39. Deferred items

Cross-school privacy-safe conflict warning, school calendar/holiday exceptions, room model, default period templates, timetable Excel import and Flutter.

## 40. Remaining risks

Validity overlap remains service-enforced and must not be bypassed by future write paths. Day copy subject mapping assumes at most one applicable current target assignment per subject; future co-teaching requires an explicit choice contract. Production TLS/secrets remain deployment work.

## 41. Teacher UI current/next/today status

Teacher “Current Lesson / Next Lesson / Today's Classes / Weekly Schedule” is now API-backed and safe to design against. Flutter was not started.

## 42. Final decision

**SPRINT 4.7 TIMETABLE ACCEPTED — READY FOR BACKEND UX CONTRACT**

No git add, commit or push was performed.

## Sprint 4.7.1 Hardening

- Daily attendance state now uses eligible/enrolled versus recorded counts per Classroom+Section/day; multiple lessons share the same state and no per-entry queries are used.
- Attendance actions are Teacher-only, writable-context, owned-assignment and current-date safe; Student/Parent/Admin/historical outputs are false.
- Working-day removal, used-period kind mutation, and used-period deletion are controlled validation failures.
- Bulk and copy operations validate one projected final state after all logical clears, preserving clear+move and swap while rejecting payload/internal conflicts atomically.
- `validate_only` and `clear_target` do not mutate the database and have preview/save parity for copy day/week.
- Targeted: 19/19 PASS. Full Core: 609/609 PASS. Coverage: 93% (10,925 statements, 770 missing). Teacher Today budget: 8 bounded queries.
- Django check, migration drift, Ruff and OpenAPI: PASS / none / PASS / 0 errors and 0 warnings.
- Bell schedule versioning remains deferred; changing a period time affects all dates using it.

**SPRINT 4.7.1 HARDENING ACCEPTED — READY FOR COMMIT**
