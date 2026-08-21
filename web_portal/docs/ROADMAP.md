# School Admin Web Portal — Roadmap V3

**Scope:** School Admin Web Portal only. Platform Owner / subscriptions are a later project.

## Repository boundaries

- `backend/` — existing Django source of truth.
- `mobile_app/` — protected parallel Flutter work. The Web agent must not modify it.
- `web_portal/` — all School Admin Web code, documentation, design references, prompts, and acceptance reports.

## Documentation layout

```text
web_portal/
├── docs/
│   ├── ROADMAP.md
│   ├── API_CAPABILITY_MATRIX.md
│   ├── API_GAP_REPORT.md
│   ├── ARCHITECTURE.md
│   ├── prompts/
│   └── acceptance/
├── design/
│   ├── nano/
│   └── references/
├── src/
├── public/
└── README.md
```

## Reviewed baseline

The reviewed uploaded snapshot was on `main` at HEAD `75c69aa`.
Flutter Student Attendance is being developed in parallel, so every Web phase must re-read the live HEAD and working tree before changes.

Backend reviewed capabilities include authentication/context, timetable administration, attendance APIs, homework, exams/results, announcements, school inbox, conversations/messages, and notifications.

Important Web gaps identified in the reviewed snapshot include customer-facing CRUD APIs for portions of academic master data and people management, plus a production Excel Import/Export Center.

## Non-negotiable rules

1. Current Backend implementation/API behavior is the functional source of truth.
2. Nano-approved boards are the visual source of truth.
3. Never invent an endpoint in React.
4. Never trust a client-supplied school ID to establish tenant scope.
5. Historical contexts are read-only.
6. Never modify `mobile_app/` from the Web workstream.
7. Never run `git clean/reset/restore` on unrelated work.
8. Backend changes require an explicit phase and tests.
9. Excel import always uses validate → preview → explicit commit.
10. No automatic publishing of exam results imported from Excel.

# Information architecture

## Dashboard
School overview and operational alerts.

## People
- Students
- Parents / Guardians
- Teachers
- Teacher assignments

## Academic Structure
- Academic years
- Academic terms
- Classrooms
- Sections
- Subjects
- ClassSubject mappings

## Daily Operations
- Timetable
- Attendance
- Homework

## Exams & Results
- Exam types
- Exams
- Grade entry
- Approval
- Publishing
- Reports

## Communications
- Announcements
- School Inbox
- Conversations / Messages
- Notifications

## Data
- Import Center
- Export Center

## Reports
- Students
- Attendance
- Results
- Homework
- Teacher workload

## Settings
- School profile
- Branding
- Academic settings
- Communication settings

# Visual design plan

Create and freeze Nano boards before implementing each major UI family:

1. Foundation + Dashboard
2. Academic Setup
3. People
4. Timetable
5. Attendance + Homework
6. Exams + Results
7. Communications
8. Import / Export Center
9. Settings + Onboarding

The Web is desktop-first, Arabic-first RTL, tablet responsive, with a collapsible sidebar, clear top bar, professional tables, filters, pagination, column visibility, drawers for short forms, full pages for complex workflows, and consistent loading/empty/error states.

# Execution phases

## W0 — Live Baseline + API Capability Audit
Deliver:
- `docs/API_CAPABILITY_MATRIX.md`
- `docs/API_GAP_REPORT.md`

Classify each required capability as:
- SUPPORTED_NOW
- BACKEND_API_GAP
- DEFERRED

No Backend changes.

## W1 — Functional Web Foundation
Create the React/TypeScript/Vite application and implement:
- Login
- session/auth foundation
- refresh/logout
- auth/me
- contexts/current/default
- `X-School-Membership-ID`
- `409 context_required`
- unavailable context
- historical read-only state
- School Admin role guard
- RTL shell/sidebar/topbar
- school/year indicator
- shared loading/empty/error states
- placeholder dashboard only

Quality gate:
- lint
- typecheck
- tests
- production build
- real Chrome smoke against local Django API

After functional acceptance: create/freeze Nano Board 1.

## W2 — Backend School Admin Enablement
Add only approved, tenant-safe APIs needed for:
- School profile/settings
- AcademicYear / AcademicTerm
- Classroom / Section / Subject / ClassSubject
- Teacher / Parent
- Student write operations
- StudentEnrollment / StudentGuardian
- TeacherAssignment
- dashboard aggregate

Requirements:
- use `request.active_*`
- historical write blocking
- tenancy tests
- OpenAPI updates
- no trust in client school ID

## W3 — Dashboard
Real aggregate data only:
- students
- teachers
- classes/sections
- attendance today
- pending result approvals
- homework
- announcements
- inbox
- timetable health

## W4 — Academic Structure
CRUD for years, terms, classrooms, sections, subjects, mappings.

## W5 — People Management
Students, enrollment/history, parents/guardians, teachers, assignments, filtered exports.

## W6 — Excel Import / Export Foundation — Mandatory V1

### Import lifecycle
`uploaded → parsed → validating → preview_ready → committed | failed | cancelled`

### Import rules
- no immediate writes after upload
- template/version validation
- normalization
- row validation
- duplicate detection
- preview
- explicit commit
- downloadable row-level errors
- active school/year scope
- audit trail
- file/row limits
- idempotency/duplicate protection

### V1 import entities
- Students + Enrollment
- Parents
- StudentGuardian links
- Teachers
- Classrooms
- Sections
- Subjects
- ClassSubject
- TeacherAssignment

### V1 exports
- Students / Enrollments
- Parents / Guardians
- Teachers / Assignments
- Academic setup
- Attendance
- Homework
- Exams/results
- Timetable

`openpyxl` may be added to Backend only in this approved phase with a pinned version and tests.

## W7 — Timetable Admin
Config, periods, grid, bulk, validate, copy, conflicts, Excel export, controlled Excel import through existing bulk/validation services.

## W8 — Attendance Admin
Daily register, class/section/date selection, bulk status, summaries, reports, XLSX export.

## W9 — Homework Management
Create/edit/publish/close, attachments, submissions, grading/return, reports/export.

## W10 — Exams & Results
Exam types, exams, grade grid, bulk grading, submit/approve/reject/reopen, publish/unpublish, logs/reports, controlled Excel grade import/export. Never auto-publish imported grades.

## W11 — Communications
Announcements, targeting, School Inbox, conversations/messages, notifications and badges.

## W12 — Reports
Academic snapshot, attendance, results, homework, teacher workload and XLSX exports.

## W13 — School Onboarding
Profile → academic year/terms → classes/sections → subjects → teachers → students → guardians → assignments → timetable → review/go-live. Reuse normal APIs/services.

## W14 — Settings & Branding
School names, logo, primary color, language, timezone and supported communication settings.

## W15 — Final Acceptance

E2E:
Login → Context → Dashboard → Academic Setup → People → Excel Import Preview/Commit → Excel Export → Timetable → Attendance → Homework → Exams/Results → Communications → Historical read-only → Logout/Login.

Must pass:
- lint/typecheck/tests/build
- Chrome smoke
- RTL
- tablet responsiveness
- long Arabic content
- tenant isolation
- historical write blocking
- import validation and duplicate protection
- export tenant scope
- no unintended `mobile_app` changes

Final decision:
`SCHOOL ADMIN WEB PORTAL V1 ACCEPTED — READY FOR PLATFORM OWNER PORTAL`

# Git discipline

Do not replace/delete the entire `web_portal` folder between phases.
Each phase updates the same project incrementally.
Do not mix Mobile, Backend, and Web changes in one commit.
