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
| Communications V1 | Codex | 🟢 ACTIVE | **Current Codex task** |
| More/Profile + Context UX | Codex | 🔴 TODO | after Communications |
| Timetable UI Closure | Codex | 🔴 TODO | existing backend/Flutter; visual/runtime closure only |
| Student Final Regression | Codex | 🔴 TODO | final pilot gate |

### Student App final target
`STUDENT APP V1 CLOSED — READY FOR SCHOOL PILOT`

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
| D3 Operational Dashboard UI implementation | Antigravity | ✅ DONE | D3.1 Executive Polish + Active Student KPI closure accepted |
| D4 Context Selector UI implementation | Antigravity | ✅ DONE | Multi-school, historical read-only, default context accepted |
| D5 System States UI implementation | Antigravity | 🟠 REVIEW | Implemented 12 state families, all gates passed, awaiting acceptance |
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
**Student Communications V1**

Required handoff to Supervisor:
- changed files
- Backend changes
- tests
- flutter analyze/test
- device screenshots/video
- online/offline/deep links
- status recommendation

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
