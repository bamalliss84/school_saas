# CODEX_CURRENT_TASK.md

Read:
- `SCHOOL_SAAS_MASTER_EXECUTION_PLAN.md`
- `PROJECT_EXECUTION_BOARD.md`
- `CODEX_STUDENT_V1_HANDOFF.md`
- existing Student closure/API/architecture docs referenced by the handoff.

## CURRENT TASK
**M1.3 — Student Timetable UI Closure — CLOSED / SUPERVISOR ACCEPTED**

Reuse the existing Backend and Flutter Timetable implementation. Close only:
- Today/Week visual and ordering behavior
- Backend-authoritative Current/Next presentation
- configured, empty-day, no-next, error, and cached-offline states
- membership/year cache isolation and recovery
- historical view-only UX
- compact 320×480, 150% text, long Arabic labels, and RTL
- Home-to-Timetable and Android Back behavior
- focused automated verification and Android runtime handoff

Do not modify Backend unless a proven contract gap exists. Do not start Student final regression or Teacher App automatically.

M1.3 is complete. Do not start M1.4 Student App Final Regression until explicitly authorized.
