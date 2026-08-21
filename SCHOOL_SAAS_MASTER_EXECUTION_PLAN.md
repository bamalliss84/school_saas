# SCHOOL_SAAS_MASTER_EXECUTION_PLAN.md
# School SaaS — Master Execution & Delivery Plan

**Purpose:** one controlled execution plan for ChatGPT (Supervisor), Codex (Mobile Apps), and Antigravity (Web Portals), with isolated Git worktrees, explicit acceptance gates, and a single DONE tracker.

## 0. Governance

### Roles
- **ChatGPT — Project Supervisor / Integration Owner**
  - owns architecture decisions, phase order, acceptance criteria, conflict resolution, and DONE status.
  - reviews Codex/Antigravity reports, screenshots, test results, backend contract changes, and merge readiness.
  - no phase becomes DONE only because an agent says it is done.

- **Codex — Mobile Delivery Agent**
  - owns Flutter delivery for:
    1. Student App V1 closure
    2. Teacher App V1
    3. Parent App V1
  - may propose narrowly-scoped Backend enablement only when proven necessary.
  - must not work on `web_portal/` or `platform_portal/`.

- **Antigravity — Web Delivery Agent**
  - owns:
    1. School Admin Web Portal
    2. Platform Owner / Subscriptions Web Portal
  - may propose narrowly-scoped Backend enablement only in approved Backend phases.
  - must not modify `mobile_app/`.

### Acceptance rule
A task is marked **✅ DONE** only after:
1. code implementation is complete;
2. static analysis passes;
3. automated tests pass;
4. real runtime/browser/device acceptance is performed where applicable;
5. screenshots/video or runtime evidence is reviewed by the Supervisor;
6. backend tenancy/historical/context constraints remain correct;
7. no unrelated track was modified;
8. the Supervisor explicitly marks the task DONE in `PROJECT_EXECUTION_BOARD.md`.

---

# 1. Git Isolation Model — Mandatory

Do not let Codex and Antigravity work in the same working tree.

Recommended directories:

```text
D:\projects\
├── school_saas\              # Integration / main
├── school_saas_codex\        # Codex worktree
└── school_saas_antigravity\  # Antigravity worktree
```

Recommended branches:

```text
main
agent/codex-mobile
agent/antigravity-web
```

Create once from the integration repository:

```bat
cd /d D:\projects\school_saas

git worktree add D:\projects\school_saas_codex -b agent/codex-mobile
git worktree add D:\projects\school_saas_antigravity -b agent/antigravity-web
```

## Commit policy after isolation
Once the worktrees are created:
- Codex **should commit** its own accepted atomic task changes on `agent/codex-mobile`.
- Antigravity **should commit** its own accepted atomic task changes on `agent/antigravity-web`.
- Neither agent pushes unless explicitly requested.
- The integration worktree `school_saas` remains the controlled merge point.

## Backend conflict policy
Backend changes are shared infrastructure. Therefore:
- no unapproved “helpful” Backend rewrites;
- each Backend change must be a small isolated commit with tests;
- before merging a Backend-changing commit, the Supervisor reviews its contract impact;
- Backend-changing commits are integrated **serially**, one track at a time;
- after a Backend merge, the other agent rebases/merges the updated `main` before continuing a Backend-dependent task.

This converts hidden working-tree interference into visible Git merge conflicts that can be reviewed safely.

---

# 2. Global Architecture Rules

These rules apply to all remaining work:

1. Current Backend code and approved API contracts are the functional source of truth.
2. Reuse existing APIs/services before adding new ones.
3. Tenant context remains based on:
   - `request.active_membership`
   - `request.active_school`
   - `request.active_role`
   - `request.active_academic_year`
4. Historical academic context is read-only except explicitly documented personal read markers.
5. Never mix cache/data across user / membership / school / academic year.
6. No fake offline mutations.
7. No hard-coded school-specific production data.
8. No unsafe client-trusted `school_id` scoping.
9. Existing accepted domains are audited before modification; never rebuild them from scratch.
10. Every significant feature must include relevant Loading / Empty / Error / Offline / Unauthorized / Historical states.
11. All mobile UI must remain RTL-safe, compact-screen safe, and support 150% text scaling.
12. All School Web UI is Arabic-first RTL, desktop-first, tablet-responsive.
13. Excel Import/Export is mandatory for School Admin Web V1.
14. Platform-owner subscription management is separate from School Admin Web.
15. New migrations are forward-only; old migrations are never edited.

---

# 3. Parallel Delivery Tracks

The project now runs on two parallel tracks.

```text
TRACK M — CODEX MOBILE
M1 Student App V1 Closure
    ↓
M2 Teacher App V1
    ↓
M3 Parent App V1

TRACK W — ANTIGRAVITY WEB
W1 School Admin Web V1
    ↓
W2 Platform Owner / Subscriptions Web V1
```

The two tracks may run in parallel as long as:
- they remain in separate worktrees/branches;
- shared Backend changes go through the Backend Integration Gate;
- final releases are merged through `main`.

---

# 4. TRACK M — CODEX

# M1 — Student App V1 Closure

## Already accepted — DO NOT rebuild
- Session restore
- JWT refresh
- stale/suspended membership recovery
- active context
- scoped cache
- offline → online recovery
- logout/login recovery
- Home
- Homework functional domain
- Results functional domain
- Attendance functional/technical domain

## M1.1 — Communications V1
**Owner:** Codex  
**Priority:** CURRENT

### Notifications
- list
- unread/read state
- mark one read
- mark all read
- unread badge
- cached offline read
- deep links
- already-read notification remains tappable
- unknown/no-action graceful fallback

Deep links where Backend payload supports:
- homework
- result
- announcement
- conversation
- school support

### Announcements
- list/detail
- correct school/class targeting
- read state
- attachments where supported
- offline cache
- historical read-only
- notification deep link
- loading/empty/error/offline

### Messages
- conversation list
- teacher/student conversation detail
- send/receive
- read state
- timestamps
- approved attachments
- cached offline history
- no offline send queue
- no student-to-student chat
- no free-form group chat
- preserve Backend authorization/concealment rules

### School Support
- create
- type
- description
- history
- status
- school replies
- detail
- deep link
- cached reads
- create/reply online only
- partial-success semantics when request succeeds but attachment fails

### Acceptance
- targeted Backend tests if changed
- Flutter tests
- compact 320×480 + 150% text regression
- runtime online/offline/deep-link smoke

---

## M1.2 — More / Profile + Context UX
- profile
- current school
- academic year
- classroom/section
- student number
- context/school change
- previous academic history
- historical read-only
- unavailable school
- no active context
- `context_required`
- session expired
- appearance/font persistence
- Help
- About
- Logout
- identity fields read-only

---

## M1.3 — Timetable UI Closure
Existing backend + Flutter are reused.

Finish only:
- Today/Week visual closure
- Current/Next
- empty day
- unpublished/no-data
- offline
- historical read-only
- compact + 150% text
- Android runtime smoke

---

## M1.4 — Student App Final Regression

Journey:

```text
Login
→ context
→ home
→ timetable
→ homework
→ results
→ attendance
→ notifications
→ announcement
→ messages
→ school support
→ profile
→ context switch
→ historical read-only
→ offline reads
→ online recovery
→ logout/login
```

Gate:

Backend:
- `python manage.py check`
- migration consistency
- changed-domain tests
- relevant core tests
- tenant isolation
- historical-write regression

Flutter:
- `flutter analyze`
- `flutter test`
- no RenderFlex overflow
- no async BuildContext lint
- no package/import errors

Runtime:
- Android emulator/phone
- online
- offline
- recovery
- deep links
- logout/login

Final allowed statement only if true:

`STUDENT APP V1 CLOSED — READY FOR SCHOOL PILOT`

---

# M2 — Teacher App V1

**Start only after M1 is Supervisor-DONE.**

## M2.0 — Audit & Contract Freeze
Audit current Backend and Flutter role-aware code.
Create:
- Teacher capability matrix
- API gap report
- role/permission map
- accepted Nano/UI references

Do not build until the audit separates existing functionality from real gaps.

## M2.1 — Teacher Foundation
- login/session/context
- teacher role guard
- school/year context
- historical read-only
- offline-safe read foundation
- teacher home/dashboard
- navigation/state system

## M2.2 — Teacher Timetable
- today/week
- current/next lesson
- assigned classes/subjects only
- offline cache
- historical viewing

## M2.3 — Teacher Attendance
- assigned class/section access only
- daily attendance
- bulk mark where Backend permits
- save/retry semantics
- no fake offline writes
- historical write blocked

## M2.4 — Teacher Homework
- create/edit draft
- publish/close
- submission modes
- attachments
- view submissions
- grade/return
- correct assignment scope

## M2.5 — Teacher Exams & Results
- assigned exams/subjects
- grade entry
- draft/save
- submit for approval
- result status
- teacher feedback
- publish only if role/Backend allows
- historical safe behavior

## M2.6 — Teacher Communications
- conversations
- students/parents only as Backend permits
- announcements/notifications
- attachments
- read states
- no unauthorized recipient discovery

## M2.7 — Teacher Profile / More
- teacher profile
- assignment summary
- context
- help/about/logout
- session states

## M2.8 — Teacher V1 Final Regression
Full role/tenant/assignment restriction regression.
Final statement only if true:

`TEACHER APP V1 CLOSED — READY FOR SCHOOL PILOT`

---

# M3 — Parent App V1

**Start only after M2 is Supervisor-DONE.**

## M3.0 — Audit & Contract Freeze
- parent API capability matrix
- children/guardian scope map
- current UI references
- Backend gaps

## M3.1 — Parent Foundation
- login/session/context
- parent role guard
- child switcher
- school/year context
- historical read-only
- offline read cache
- parent home

## M3.2 — Child Overview
For selected child:
- identity/school/class
- today summary
- attendance
- homework
- results
- notices

No cross-child cache leakage.

## M3.3 — Attendance
- child attendance history
- daily details
- filters
- offline cache

## M3.4 — Homework
- child homework
- status/submission visibility allowed by contract
- teacher attachments
- offline reads

## M3.5 — Results
- published results only
- term/subject/exam type
- detail
- teacher note
- offline cache

## M3.6 — Communications
- school announcements
- notifications/deep links
- parent-school/teacher conversations where authorized
- school support if Parent scope is approved

## M3.7 — Profile / Children / Context
- parent profile
- linked children
- child switch
- school/year history
- unavailable context
- help/about/logout

## M3.8 — Parent V1 Final Regression
Final statement only if true:

`PARENT APP V1 CLOSED — READY FOR SCHOOL PILOT`

---

# 5. TRACK W — ANTIGRAVITY

# W1 — School Admin Web Portal V1

## W1.0 — Functional Foundation
Current state: implemented and accepted earlier.

Includes:
- React/TypeScript/Vite
- auth/session
- refresh/logout
- auth/me
- context foundation
- `X-School-Membership-ID`
- role guard
- historical state
- shell foundation
- lint/typecheck/tests/build

## W1.1 — Visual Foundation Closure
### DONE/approved so far
- D1 Login — implementation + scale correction
- D2 Main Shell — implementation + route active-state fix + density correction

### Remaining
- D3 Operational Dashboard implementation
- D4 Context Selector implementation
- D5 System States implementation
- D6 Responsive System implementation

Each D-stage:
Design approved → implement → browser review → Supervisor DONE → next.

No automatic jump across D stages.

---

## W1.2 — Backend School Admin Enablement Pack

After visual foundation closes, audit and add only proven missing customer-facing APIs:
- school profile/settings
- AcademicYear
- AcademicTerm
- Classroom
- Section
- Subject
- ClassSubject
- Teacher
- Parent
- Student write operations
- StudentEnrollment
- StudentGuardian
- TeacherAssignment
- dashboard aggregate

All APIs:
- active-context scoped
- tenant-safe
- historical write-blocked
- tested
- OpenAPI documented

---

## W1.3 — Dashboard Real Data
Replace visual placeholder values with real API data.
Prefer aggregate endpoint(s); avoid request fan-out.
No hard-coded demo KPIs.

---

## W1.4 — Academic Structure
- years
- terms
- classrooms
- sections
- subjects
- mappings

Professional tables/forms/filters.

---

## W1.5 — People Management
- students
- enrollment/history
- parents/guardians
- teachers
- assignments
- status/activation
- filtered exports

---

## W1.6 — Excel Import / Export Foundation — Mandatory

Import lifecycle:

```text
uploaded
→ parsed
→ validating
→ preview_ready
→ committed | failed | cancelled
```

Rules:
- upload does not immediately write
- template/version validation
- normalization
- duplicate detection
- preview
- explicit commit
- downloadable row errors
- active tenant/year scope
- audit trail
- file/row limits
- idempotency
- formulas treated safely
- no auto-publish of results

V1 imports:
- Students + Enrollment
- Parents
- StudentGuardian
- Teachers
- Classrooms
- Sections
- Subjects
- ClassSubject
- TeacherAssignment

V1 exports:
- People
- Academic setup
- Attendance
- Homework
- Exams/results
- Timetable

---

## W1.7 — Timetable Admin
- config/periods/grid
- bulk
- validate
- copy
- conflicts
- XLSX export
- controlled Excel import through existing validation services

## W1.8 — Attendance Admin
- daily register
- class/section/date
- bulk actions
- summaries/reports
- XLSX export

## W1.9 — Homework Admin
- create/edit
- publish/close
- attachments
- submissions
- grading/return
- report/export

## W1.10 — Exams & Results
- ExamType
- exams
- grade grid
- bulk grade
- submit/approve/reject/reopen
- publish/unpublish
- reports/logs
- Excel export
- controlled grade import preview
- never auto-publish imported grades

## W1.11 — Communications
- announcements
- targeting
- School Inbox
- conversations/messages
- notifications
- badges

## W1.12 — Reports
- students
- attendance
- results
- homework
- teacher workload
- XLSX

## W1.13 — School Onboarding
Profile → academic setup → people → assignments → timetable → review/go-live.
Reuse normal services/APIs.

## W1.14 — Settings & Branding
- school names
- logo
- primary color
- language
- timezone
- supported communications settings

## W1.15 — School Web Final Acceptance
Final allowed statement only if true:

`SCHOOL ADMIN WEB PORTAL V1 CLOSED — READY FOR SCHOOL PILOT`

---

# W2 — Platform Owner / Subscriptions Web V1

**Start after School Admin Web W1 is Supervisor-DONE.**

This is a separate portal for the SaaS owner, not school staff.

## W2.0 — Business/Backend Audit
Freeze:
- tenant lifecycle
- subscription lifecycle
- plans
- limits
- trial
- suspension
- renewal
- payments/manual deposits if applicable
- owner permissions

## W2.1 — Owner Authentication & Shell
- owner-only guard
- platform dashboard shell
- secure context separate from school context

## W2.2 — Schools / Tenants
- schools list
- school detail
- create/onboard
- activate/suspend
- plan
- dates/status
- usage snapshot

## W2.3 — Plans
- plans
- features
- limits
- pricing
- activation rules
- version-safe plan changes

## W2.4 — Subscriptions
- subscription status
- start/end
- trial
- renew
- pause/suspend
- change plan
- history/audit

## W2.5 — Payments / Collections
Only after business policy is frozen.
- payment records
- manual deposit/reference
- status
- receipt/evidence if required
- reconciliation workflow
- no unsafe automatic accounting assumptions

## W2.6 — Usage / Limits
- students
- teachers
- storage if supported
- active users
- feature limits
- approaching-limit alerts

## W2.7 — Platform Dashboard
- total schools
- active subscriptions
- trials
- expiring subscriptions
- suspended
- usage
- operational alerts

## W2.8 — Owner Reports / Excel
- tenants
- subscriptions
- renewal/expiry
- payments
- usage
- XLSX export

## W2.9 — Owner Portal Final Regression
Final allowed statement only if true:

`PLATFORM OWNER PORTAL V1 CLOSED — READY FOR COMMERCIAL PILOT`

---

# 6. Backend Integration Gate

Any task that needs Backend changes must produce:

1. exact gap;
2. affected endpoints/models;
3. why existing API cannot satisfy it;
4. proposed contract;
5. tenancy implications;
6. historical-mode implications;
7. migration need YES/NO;
8. tests;
9. OpenAPI/docs changes;
10. dedicated atomic commit.

Supervisor decision:
- APPROVE
- MODIFY
- REJECT

No other agent changes the same Backend area until the commit is integrated.

---

# 7. Integration / Merge Cycle

After Supervisor accepts an atomic task:

1. Agent creates a clean task commit in its own worktree.
2. Integration worktree:
   ```bat
   cd /d D:\projects\school_saas
   git checkout main
   ```
3. Merge/cherry-pick only accepted commit(s).
4. Run shared quality checks appropriate to the changes.
5. If Backend changed, both agent branches sync from updated `main`.
6. Update `PROJECT_EXECUTION_BOARD.md`.
7. Mark task **✅ DONE** only after successful integration.

---

# 8. Definition of Done

A phase is DONE only when all relevant criteria are true:

### Code
- no placeholder production behavior
- no fake runtime metrics
- no unrelated rewrites
- clean boundaries

### Backend
- checks/tests
- no missing migrations
- tenant isolation
- historical restrictions

### Mobile
- analyze
- tests
- compact/150%
- runtime

### Web
- lint
- typecheck
- tests
- build
- real Chrome visual/runtime smoke
- responsive where required

### Product
- accepted design contract
- functional acceptance
- docs/status updated

---

# 9. Delivery Order

Parallel preferred schedule:

```text
CODEX:
Student Communications
→ Student More/Profile
→ Student Timetable Closure
→ Student Final Regression
→ Teacher App
→ Parent App

ANTIGRAVITY:
School Web D3
→ D4
→ D5
→ D6
→ School Web Backend Enablement
→ Academic/People
→ Excel
→ Operations
→ Communications/Reports
→ Final School Web
→ Platform Owner Portal
```

The Supervisor reviews every closure checkpoint before either track enters the next major phase.
