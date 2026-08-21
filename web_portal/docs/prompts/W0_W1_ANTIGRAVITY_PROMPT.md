# Antigravity — School Admin Web Portal — W0 + W1

Workspace:
`D:\projects\school_saas`

## First: establish the LIVE baseline

Run read-only:
- `git rev-parse HEAD`
- `git status --short`

The previously reviewed snapshot was HEAD `75c69aa`, but Flutter Student Attendance is being developed in parallel. The live repository may therefore be newer.

## Protected work

Do NOT:
- modify anything under `mobile_app/`
- run Flutter code generation
- touch existing Nano images
- clean/reset/restore unrelated files
- stage/commit/push
- modify Backend production logic in W0/W1

Preserve all pre-existing modified/untracked files.

## Read before implementation

Read:
- `web_portal/docs/ROADMAP.md`
- root `BACKEND_UX_CONTRACT_V1.md`
- root `BACKEND_UX_CONTRACT_REPORT.md`
- root `API_CONTRACT_V1.md`
- root `AGENTS.md`
- root `ROADMAP.md`
- `backend/config/api_urls.py`
- relevant Backend auth/context/permission implementation
- current OpenAPI/schema if available

Current Backend code/API behavior is the functional source of truth.

# Execute ONLY W0 + W1

## W0

Create/update inside `web_portal/docs/`:
- `API_CAPABILITY_MATRIX.md`
- `API_GAP_REPORT.md`

Classify required School Admin capabilities:
- SUPPORTED_NOW
- BACKEND_API_GAP
- DEFERRED

Explicitly assess:
- authentication/context
- School Admin authorization
- academic master-data CRUD
- people CRUD
- timetable
- attendance
- homework
- exams/results
- communications
- dashboard aggregation
- Excel import/export

Do not patch Backend gaps.

## W1

Build the application inside the existing `web_portal/` folder.

Preferred stack:
- React
- TypeScript
- Vite
- React Router
- TanStack Query
- React Hook Form
- Zod only when useful

Arabic-first RTL, desktop-first, tablet responsive, centralized design system.

Implement ONLY:
- Login
- auth/session foundation
- token refresh/logout
- auth/me
- contexts/current/default
- `X-School-Membership-ID`
- `409 context_required` UX
- unavailable context
- historical read-only state/banner
- School Admin role guard
- application shell
- RTL sidebar
- topbar
- current school/year indicator
- loading/empty/error components
- placeholder Dashboard only

Do NOT implement business modules yet.

## Networking

Prefer a Vite development proxy to local Django when practical.
Do not weaken Django with wildcard CORS.
Do not disable browser security.

## Security

- never store passwords
- no hardcoded demo credentials
- document browser token-storage strategy and tradeoffs
- production Web auth hardening remains an explicit release gate if needed

## Documentation location

Keep Web documentation inside `web_portal/docs/`.

Create/update:
- `web_portal/README.md`
- `web_portal/docs/ARCHITECTURE.md`
- `web_portal/docs/acceptance/PHASE_W1_ACCEPTANCE.md`

Do not create duplicate Web roadmap/report files in the repository root.

## Design folders

Preserve/use:
- `web_portal/design/nano/`
- `web_portal/design/references/`

Do not claim final visual acceptance. Nano Web Board 1 comes after W1 functional acceptance.

## Checks

Run:
- npm install
- lint
- typecheck
- tests
- production build
- real Chrome smoke against Django Demo API when possible

## Git safety

Do not:
- git add
- git commit
- git push
- git reset
- git restore
- git clean

At end:
- `git status --short`
- `git diff --stat`
- `git diff --check`

Clearly separate pre-existing changes from Web changes.

## Final response

Report:
- live HEAD at start
- pre-existing work preserved
- stack
- architecture
- files created/changed
- API capability/gap summary
- Login status
- Context status
- School Admin role guard status
- Chrome status
- lint/typecheck/tests/build
- Backend changes YES/NO
- Backend migrations YES/NO
- `mobile_app` changes caused by this task YES/NO
- git summary

Final decision exactly one:

`WEB PORTAL W1 FUNCTIONALLY ACCEPTED — READY FOR NANO WEB BOARD 1`

or

`WEB PORTAL W1 REJECTED — FIXES REQUIRED`

Then STOP.
