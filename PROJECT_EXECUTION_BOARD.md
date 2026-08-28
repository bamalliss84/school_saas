# PROJECT_EXECUTION_BOARD.md
# School SaaS — Supervisor Status Board

**Status vocabulary**
- ✅ DONE — Supervisor accepted
- 🟢 ACTIVE — current agent task
- 🟠 REVIEW — implementation done, awaiting Supervisor/runtime acceptance
- 🔴 TODO — not started
- 🟡 DEFERRED — intentionally postponed
- ⛔ BLOCKED — cannot proceed

> Only ChatGPT/Supervisor acceptance changes a task to ✅ DONE.

---

# TRACK M — CODEX MOBILE

## Student App V1

| Task | Owner | Status | Notes |
|---|---|---:|---|
| Foundation/session/context/cache | Codex | ✅ DONE | Accepted existing work |
| Home | Codex | ✅ DONE | Existing and working |
| Homework | Codex | ✅ DONE | Functional closure accepted |
| Results | Codex | ✅ DONE | Functional closure accepted; ExamType metadata normalization remains controlled follow-up |
| Attendance | Codex | ✅ DONE | Functional + technical acceptance; do not rebuild |
| Communications V1 | Codex | ✅ DONE | Supervisor runtime accepted on Android Emulator |
| More/Profile + Context UX | Codex | ✅ DONE | Supervisor runtime accepted: multi-context selection/current identification, historical switching/banner/read-only enforcement, and topbar refresh |
| Timetable UI Closure | Codex | ✅ DONE | Supervisor runtime accepted on Android Medium Phone, including responsive RTL Week selector |
| Student Final Regression | Codex | ✅ DONE | M1.4 Supervisor runtime accepted, including Results state/navigation recovery |

### Student App final target
`STUDENT APP V1 CLOSED — READY FOR SCHOOL PILOT`

**Status: ✅ CLOSED / DONE — SUPERVISOR ACCEPTED**

---

## Teacher App V1

| Task | Status |
|---|---:|
| Audit & Contract Freeze | 🔴 TODO |
| Foundation | 🔴 TODO |
| Timetable | 🔴 TODO |
| Attendance | 🔴 TODO |
| Homework | 🔴 TODO |
| Exams/Results | 🔴 TODO |
| Communications | 🔴 TODO |
| Profile/More | 🔴 TODO |
| Final Regression | 🔴 TODO |

---

## Parent App V1

| Task | Status |
|---|---:|
| Audit & Contract Freeze | 🔴 TODO |
| Foundation + Child Switch | 🔴 TODO |
| Child Overview | 🔴 TODO |
| Attendance | 🔴 TODO |
| Homework | 🔴 TODO |
| Results | 🔴 TODO |
| Communications | 🔴 TODO |
| Profile/Children/Context | 🔴 TODO |
| Final Regression | 🔴 TODO |

---

# TRACK W — ANTIGRAVITY WEB

## School Admin Web V1

| Task | Owner | Status | Notes |
|---|---|---:|---|
| W0 API audit | Antigravity | ✅ DONE | capability/gap docs exist |
| W1 functional foundation | Antigravity | ✅ DONE | lint/typecheck/tests/build accepted |
| D1 Login UI | Antigravity | ✅ DONE | implemented + desktop scale correction + manual review |
| D2 Main Shell UI | Antigravity | ✅ DONE | active-route fix + density correction + manual review |
| D3 Operational Dashboard UI implementation | Antigravity | 🟢 ACTIVE | **Current Antigravity task** |
| D4 Context Selector UI implementation | Antigravity | 🔴 TODO | approved Nano exists |
| D5 System States UI implementation | Antigravity | 🔴 TODO | approved Nano exists |
| D6 Responsive System implementation | Antigravity | 🔴 TODO | approved Nano exists |
| Backend School Admin Enablement | Antigravity | 🔴 TODO | shared Backend gate |
| Dashboard real data | Antigravity | 🔴 TODO | no hard-coded demo metrics |
| Academic Structure | Antigravity | 🔴 TODO | |
| People Management | Antigravity | 🔴 TODO | |
| Excel Import/Export Center | Antigravity | 🔴 TODO | mandatory V1 |
| Timetable Admin | Antigravity | 🔴 TODO | |
| Attendance Admin | Antigravity | 🔴 TODO | |
| Homework Admin | Antigravity | 🔴 TODO | |
| Exams/Results | Antigravity | 🔴 TODO | |
| Communications | Antigravity | 🔴 TODO | |
| Reports | Antigravity | 🔴 TODO | |
| Onboarding | Antigravity | 🔴 TODO | |
| Settings/Branding | Antigravity | 🔴 TODO | |
| Final Regression | Antigravity | 🔴 TODO | |

### School Web final target
`SCHOOL ADMIN WEB PORTAL V1 CLOSED — READY FOR SCHOOL PILOT`

---

## Platform Owner / Subscriptions Web V1

| Task | Status |
|---|---:|
| Business/API Audit | 🔴 TODO |
| Owner Auth/Shell | 🔴 TODO |
| Schools/Tenants | 🔴 TODO |
| Plans | 🔴 TODO |
| Subscriptions | 🔴 TODO |
| Payments/Collections | 🔴 TODO |
| Usage/Limits | 🔴 TODO |
| Platform Dashboard | 🔴 TODO |
| Reports/Excel | 🔴 TODO |
| Final Regression | 🔴 TODO |

### Owner Portal final target
`PLATFORM OWNER PORTAL V1 CLOSED — READY FOR COMMERCIAL PILOT`

---

# SHARED BACKEND INTEGRATION LOCK

**Current lock:** NONE

When a track needs Backend changes, fill:

```text
LOCK OWNER:
TASK:
FILES/DOMAIN:
START:
STATUS:
```

Only one Backend-changing integration window should be active at a time.

---

# NEXT SUPERVISOR CHECKPOINTS

### Codex
Current:
**Student Mobile V1: ✅ CLOSED / DONE — SUPERVISOR ACCEPTED. Teacher App M2 is the next official Mobile milestone and has not started.**

M1.4 review:
- ✅ authentication/session/context and scoped offline architecture retained
- ✅ Home, Timetable, Homework, Results, Attendance, Communications, and More/Profile integration reviewed
- ✅ historical read-only and user/membership/academic-year isolation retained
- ✅ nested Android Back corrected for Homework, Results, Conversations, and Attendance detail
- ✅ Results refresh no longer flashes stale values; first-tap detail and Back navigation are reliable
- ✅ final Supervisor online/offline/recovery/context-switch journey accepted

M1.3 closure:
- ✅ Today/Week ordering, Current/Next, and distinct empty states
- ✅ scoped cached offline recovery and membership/year isolation
- ✅ historical view-only, RTL, 320×480 at 150%, and nested Back handling
- ✅ Supervisor Android Medium Phone runtime acceptance, including all seven fully visible RTL weekday chips with no clipping/overflow

M1.2 More/Profile + Context UX closure:
- ✅ Supervisor runtime accepted
- ✅ multi-context selector and current-context identification
- ✅ historical selection, banner, and read-only enforcement
- ✅ topbar/context refresh and switching behavior

Communications V1 closure:
- ✅ Supervisor runtime accepted on Android Emulator
- ✅ online recovery and cached offline behavior
- ✅ School Support creation UI and existing conversation rows
- ✅ Arabic RTL, keyboard handling, and no observed RenderFlex overflow

Next Codex task remains subject to its documented dependencies and gates.

### Antigravity
Current:
**School Web D3 Operational Dashboard implementation**

Required handoff:
- changed files
- actual Chrome screenshot/video
- real vs unavailable dashboard metrics
- API gaps
- lint/typecheck/tests/build
- no mobile changes
- status recommendation

Supervisor reviews each and updates this board.
