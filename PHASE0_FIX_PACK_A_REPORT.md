# Phase 0 — Fix Pack A (Acceptance Findings Only)

Baseline: `a892ba9` (Phase 1 + Drift test fix).

## Guardrail
No new feature, no Nano redesign, no homework/results business-rule change, no context architecture change. This pack only fixes failures observed during Android 15 emulator acceptance.

## Confirmed acceptance findings before the pack
- Session restore: PASS.
- Logout A → Login B: PASS.
- Logout persistence: PASS.
- Online → Offline → Online recovery: PASS.
- Timetable navigation: PASS.
- Homework and Results RTL score semantics: PASS (`9/10`, `18/20 = 90%`).
- Offline cold start: FAIL — returned to login.
- Offline cache indicator: FAIL — cached data could be shown without a clear offline state until a refresh occurred.
- Bottom navigation: FAIL — homework/results reopened stale detail after leaving the tab.
- Appearance: persistence PASS, but font selection recreated routing and jumped to Home.
- Suspended membership: backend enforcement PASS and 403 was not treated as offline; Flutter recovery/Arabic UX was incomplete.
- Access-token expiry/refresh: pending by user choice.

## Fixes implemented
1. Local non-secret session snapshot (user identity + selected context only). JWTs remain in secure storage. Offline bootstrap uses the snapshot only when stored tokens exist and context discovery fails with a real network error.
2. API network callbacks mark the authenticated session offline/online. Student shell shows the existing OfflineCacheBanner consistently; entering data tabs triggers refresh so loss of connectivity is detected.
3. 403 now triggers context revalidation through the context-independent `/auth/contexts/` path. Invalid stored membership is cleared; if no usable context remains the app moves to a neutral Arabic unavailable-context state. Raw English 403/404 messages are not exposed.
4. Selecting Homework or Results from bottom navigation explicitly closes nested detail state before showing the tab root.
5. Font selection no longer rebuilds/recreates the GoRouter because font changes are isolated below the router owner. Preference persistence remains unchanged.
6. Android `compileSdk` pinned to 35 to satisfy `sqlite3_flutter_libs` and remove the build compatibility warning.
7. Added regression coverage for safe Arabic access errors and local session snapshot serialization.

## Retest gate
Run Drift generation, Flutter analyze, Flutter tests, then repeat: offline cold start, offline banner, suspended membership recovery, homework/results root reset, and font selection staying on More. Token-expiry refresh remains pending.
