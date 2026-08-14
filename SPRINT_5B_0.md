# Sprint 5B.0 — Student Design System + Offline Local Data Foundation

Baseline: `8c7899d Sprint 5A: add Flutter foundation authentication and active context`.

## Delivered scope

- Cross-platform Student design tokens, bundled Arabic fonts, reusable components, responsive `SafeArea` shell, and five-destination placeholder navigation.
- Real font setting using Shared Preferences; immediate and persistent across logout/context switch.
- Drift schema version 1, app-private database lifecycle, scoped context cache, metadata foundation, transaction-safe replacement, invalidation, and purge.
- Offline read state/policy/repository abstractions and lightweight real context/profile cache proof without Student feature data.
- Explicit logout/session-expiry cache purge while preserving appearance preferences.
- Database, repository, membership/user isolation, context-switch, rollback, historical, logout/font, RTL, Arabic overflow, and text-scale tests.

## Boundaries

No Backend change, Backend migration, Student Home, Timetable, Homework, Results, Attendance, Messaging, Notifications, Parent, or Teacher feature was implemented. Server mutations are online-only. No offline outbox exists.

## Cross-platform acceptance

The same Flutter codebase and dependencies target Android and iOS. Android build/device validation is required on this Windows host. iOS architecture and package compatibility are reviewed here; native build/simulator/device/archive verification remains pending macOS/Xcode and does not by itself reject this sprint.

Physical Android acceptance passed on Samsung SM N986U (`R5CN81DGDXJ`): APK install/launch, development API connectivity through `adb reverse`, real Demo Student authentication, and single-context routing all succeeded. Foundation offline stability passed within the data available in 5B.0. Feature-level Student dataset offline acceptance is mandatory in 5B.1.

## Decision

**SPRINT 5B.0 DESIGN & OFFLINE FOUNDATION ACCEPTED — READY FOR STUDENT HOME & TIMETABLE**

## Next sprint

Sprint 5B.1: Student Home + Timetable + real feature-local cache. Do not begin without approval.
