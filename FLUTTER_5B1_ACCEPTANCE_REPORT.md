# Flutter Sprint 5B.1 Acceptance Report

- Baseline: accepted Sprint 5B.0 working tree on commit baseline `8c7899d`.
- Scope: Student Home, Today/Week timetable, backend-authoritative Current/Next, real Drift cache, historical read-only behavior.
- API: production `timetable/today/`, `week/`, `current/`, `next/`; all requests use the shared membership-aware ApiClient.
- Models: typed period/entry/today/day/week models; nullable Current/Next are valid empty states.
- Breaks: rendered from Today `periods` as distinct non-lesson timeline rows.
- Local DB: schema v2; additive `CachedTimetableDatasets`; scope is local user + membership + academic year + dataset key.
- Security: read-only Student feature; no mutation UI, outbox, offline writes, credentials, or authorization data in SQLite.
- State: loading, fresh/cached, refreshing, offline cached, and controlled error through Riverpod controller.
- Cache behavior: local-first, four bounded API reads, parse before one transactional cache replacement, retain old cache on failure.
- Context isolation: tested membership A/B; user isolation and logout purge remain covered by shared DB tests.
- Historical: shared historical banner and read-only timetable presentation; no write controls.
- `dart format lib test`: PASS.
- `flutter analyze`: PASS — no issues.
- `flutter test`: PASS — 26/26, including long Arabic student/school names at 150% scaling across Tajawal, Cairo, and Noto Sans Arabic.
- Debug APK: PASS. Existing compileSdk 34/`sqlite3_flutter_libs` SDK 35 warning remains a documented mobile maintenance item; build succeeds and dependencies were not upgraded.
- Physical device: Samsung SM N986U, Android 13, device `R5CN81DGDXJ`.
- Real online: `adb reverse`, real `demo_student_a_01` login, single context, Home, Today, Week, Current/Next, and cache population PASS.
- Real offline: removed reverse, refreshed timetable, cached rows remained, offline banner and last-updated appeared, no crash/logout; restored reverse, refreshed, fresh state returned and banner disappeared — PASS.
- Week UX: horizontal readable day selector and vertical lessons verified on device. RTL, SafeArea, fixed bottom navigation, long Arabic/150% automated coverage PASS.
- iOS: package/shared architecture review PASS; native macOS/Xcode gate pending and non-blocking on Windows.
- Backend production changes: NONE. Backend migrations: NONE. Backend suite not rerun.
- Nano visual reference: received and reviewed against the Student UI board and the shared Authentication/Context identity board.
- Visual QA: PASS — Arabic RTL, `#3157D5` primary, `#F7F8FC` background, white cards, text hierarchy, compact density, five-destination bottom navigation, context header, historical read-only treatment, and subtle cached-data treatment align with the approved production-quality interpretation.
- Presentation-only closeout: added academic year to the context header, differentiated Current (success accent) from Next (primary accent) while keeping finished/list rows neutral, and replaced the heavy offline Material banner with a compact two-line cache banner. API, domain, repository, Drift schema, and offline behavior were unchanged.
- Device visual smoke: the prior Samsung physical-device Home/Today/Week/offline evidence remains valid; the device was not visible to ADB during this final reference-review pass.
- Debug APK after visual changes: PASS. The first attempts hit a Windows lock on generated build assets; a clean build directory completed successfully. The existing compileSdk maintenance warning remains non-blocking.
- Git: final status/check recorded after documentation.

## Final decision

**SPRINT 5B.1 STUDENT HOME & TIMETABLE ACCEPTED — READY FOR HOMEWORK**
