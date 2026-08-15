# Flutter Sprint 5B.2 Acceptance Report

- Baseline: `56cf542 Sprint 5B: add student design offline foundation and timetable`.
- Functional source: production Homework APIs and `BACKEND_UX_CONTRACT_V1.md`; Nano Student Homework board is the visual source.
- Real endpoints: `students/me/homework/`, `homework/<id>/`, `homework-submissions/`, draft creation/update, and `final-submit/`.
- Lifecycle: backend `completion_status` and `can_create_draft`/`can_edit`/`can_final_submit` flags drive UI; Flutter does not recreate permissions.
- Drift: schema v3 additive `CachedHomeworkItems` and `LocalHomeworkDrafts`; every row is scoped by local user, membership, academic year, and homework ID.
- Local Draft: answer, device-only personal note, and file references persist across tab/restart/offline; they are never represented as server submission state.
- Submit: online-only; server draft creation/update/final confirmation precede local-draft deletion. Network failure preserves the draft.
- Attachments: metadata is cached in SQLite; bytes are downloaded only online to the platform-safe app-private documents directory. No bytes enter SQLite and no large file-opening/cache engine was introduced.
- Historical: list/detail/grade/feedback remain readable; draft/edit/submit/download mutation controls follow read-only/network constraints.
- Logout: current-user Homework cache and drafts purge; another user/context is isolated and font preference survives.
- Visual QA: Nano reference readable and reviewed; RTL, `#3157D5`, `#F7F8FC`, white rounded cards, compact filters/status chips, primary action, typography, and density PASS.
- Responsive QA: long Arabic title/feedback patterns and 150% text-scale widget coverage PASS; Samsung SafeArea/bottom navigation physical flow PASS.
- Dependency: `path_provider 2.1.5` changed from transitive to direct only; the already locked Android and iOS/Foundation implementations remain compatible with the current Flutter/Dart stack. No dependency upgrade occurred.
- Static/build: format PASS; analyze PASS; 36/36 tests PASS; Debug APK PASS.
- Physical Android: Samsung SM N986U (`R5CN81DGDXJ`), `adb reverse`, and `API_BASE_URL=http://127.0.0.1:8000/api/v1/`.
- Online E2E: `demo_student_a_02` login, real list/detail, draft persistence after tab and app restart, recovery refresh, create/update/final-submit, and `submitted` state PASS.
- Offline E2E: reverse removed; cached list/detail and Local Draft remained; offline banner displayed; final submit was blocked with the required safe message; reverse restored and data refreshed — PASS.
- Returned/graded/historical behavior: covered by backend-derived parsing/presentation and targeted tests; the seeded `demo_student_a_01` graded scenario remains available, while the mutation E2E used the unsubmitted second Demo Student.
- Backend production changes: NONE. Backend migrations: NONE. Full backend suite not rerun.
- Git add/commit/push: not performed.

## Final decision

**SPRINT 5B.2 STUDENT HOMEWORK ACCEPTED — READY FOR RESULTS & ATTENDANCE**
