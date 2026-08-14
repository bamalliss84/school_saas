# Flutter Sprint 5B.0 Acceptance Report

## 1–8. Baseline, scope, dependencies, and database

- Baseline: `8c7899d Sprint 5A: add Flutter foundation authentication and active context`.
- Changed files: Flutter application and Sprint documentation only; Backend production code and Backend migrations remain unchanged.
- SDK: Flutter 3.24.5 stable; Dart 3.5.4.
- Added direct runtime dependencies: `drift 2.22.1`, `drift_flutter 0.2.4`, `shared_preferences 2.5.3`; dev: `drift_dev 2.22.1`, `build_runner 2.4.13`.
- Compatibility: versions were selected and pinned for the current SDK after a newer resolved Drift pair produced an API mismatch. Android and iOS implementations resolve through the same Flutter packages. No SDK upgrade was performed.
- Drift uses one application-scoped `AppDatabase`, generated Dart source, app-private platform documents directory, and schema version 1 with an additive migration hook and no destructive default migration.
- Minimal tables: scoped cached contexts plus cache metadata. No complete feature tables were created.
- Identity scope: `localUserKey + membershipId + academicYearKey + resourceType/resourceId`; school name and role label are not persistence keys.

## 9–19. Isolation, offline strategy, logout, and security

- User and membership isolation: tested; another local user or membership cannot query the record.
- Historical cache: supported as explicitly read-only metadata.
- Repository strategy: UI → Repository → Remote/Local data source. HTTP remains truth; cache is a durable read projection.
- Reads: stale-while-revalidate/local-first foundation with cache fallback and controlled offline-empty failure.
- Writes: server-state mutations remain online-only. No fake success, outbox, sync queue, or conflict engine.
- Cache writes: valid remote data replaces local data; list replacement is transactional; failure preserves old cache.
- Context switch: binds to the new scoped database query, never reuses the prior membership UI, and retains the other context cache.
- Logout/session expiry: tokens are cleared through existing secure session flow and current-user cache is purged. Font preference remains.
- Attachments: bytes are excluded from SQLite and future downloads must use app-private storage. Downloader/cleanup engine is deferred.
- Database encryption: not implemented. App sandbox storage, secure token separation, and logout purge are active. Mandatory encryption requires a maintained Android+iOS-compatible stack, key lifecycle, and threat-model review; no deprecated encryption package was added.
- Tokens/passwords/authorization headers/secrets: never stored in SQLite; tokens remain in `flutter_secure_storage` for Android and iOS.

## 20–29. Design system and cross-platform shell

- Theme: centralized Material 3 theme.
- Colors: primary `#3157D5`, background `#F7F8FC`, surface `#FFFFFF`, text and semantic colors centralized.
- Typography: centralized responsive scale respecting system text scaling.
- Default font: bundled Tajawal. Bundled alternatives: Cairo and Noto Sans Arabic; no runtime font network dependency.
- Font switching: immediate through Riverpod and persisted in Shared Preferences across restart/logout/context switching.
- RTL: application-wide; tested in widgets.
- Responsive/accessibility: flexible layouts, long-name overflow handling, 150% text-scale widget test, 44+ control sizing, semantic/non-color status cues.
- Student shell: shared Android/iOS Flutter shell with `SafeArea`, five required destinations, and appearance settings only; no Student business feature.
- Navigation does not depend on Android hardware-back behavior. iPhone notch/Dynamic Island/home indicator safety is represented by SafeArea; native validation remains pending macOS/Xcode.

## 30–39. Verification

- Local DB tests: PASS — open/schema, scoped insert/read, membership/user isolation, rollback, timestamp persistence, purge, historical metadata, migration hook.
- Repository offline tests: PASS — remote success/cache update, remote failure/cache fallback, no-cache controlled failure, invalid replacement preserves old cache.
- Context switch test: PASS — A only, B only, A retained.
- Logout cache/font test: PASS.
- `flutter pub get`: PASS. Available updates are not failures; compatible versions remain pinned.
- `dart format lib test`: PASS; no pending formatting changes.
- `flutter analyze`: PASS — no issues.
- `flutter test`: PASS — 20/20.
- Debug APK: PASS — `build/app/outputs/flutter-apk/app-debug.apk`. Build warned that transitive `sqlite3_flutter_libs` requests compile SDK 35 while the project uses 34, but Gradle completed successfully; align compile SDK in a future mobile-only maintenance change before release.
- Physical Android device: PASS — Samsung SM N986U (`R5CN81DGDXJ`). `flutter run` installed and launched the APK successfully.
- Development connectivity: PASS using `adb reverse tcp:8000 tcp:8000` (`UsbFfs tcp:8000 tcp:8000`) and `API_BASE_URL=http://127.0.0.1:8000/api/v1/`.
- Real authentication: PASS — Demo Student `demo_student_a_01`; Backend login returned access/refresh tokens, Student user, one active School Noor student context, membership ID, and `has_multiple_contexts=false`. Flutter login and single-context routing succeeded on the phone.
- Foundation device stability: PASS. The app remained stable when Backend/network was unavailable; no crash or forced logout was observed. Font preference remained intact. Local database availability, cross-user isolation, membership isolation, and purge behavior remain covered by the passing Drift tests.
- Feature-level offline acceptance is intentionally deferred to Sprint 5B.1: online Student Home/Timetable load → offline cached display → online refresh requires the first real Student datasets and must not be faked in 5B.0.
- iOS architecture/package compatibility: PASS by shared-code/package review. iOS simulator, physical iPhone, secure-storage/offline/context/RTL tests, and archive validation are PENDING macOS + Xcode; this pending state is not the rejection reason.

## 40–44. Scope, risks, deferred work, and decision

- Backend changes: NONE. Backend migrations: NONE. Backend tests were not run.
- Git diff check: recorded in final repository checks after documentation completion.
- Remaining blocker: NONE for Sprint 5B.0.
- Remaining risks: Android compile SDK 35 maintenance warning; iOS native gate pending macOS/Xcode; DB encryption decision pending; attachment cache cleanup policy pending.
- Deferred: Student feature caches 5B.1–5B.4, Offline Outbox, write synchronization, conflicts, idempotency keys, biometric/PIN, file-cache cleanup.

## Final decision

**SPRINT 5B.0 DESIGN & OFFLINE FOUNDATION ACCEPTED — READY FOR STUDENT HOME & TIMETABLE**

The full feature-level offline workflow is a mandatory Sprint 5B.1 acceptance gate. Native iOS simulator/device/archive verification remains pending macOS/Xcode and is not a Windows-host blocker.
