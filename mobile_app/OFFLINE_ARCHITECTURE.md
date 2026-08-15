# Offline Architecture — Sprint 5B.0

## Source of truth and read policy

Django remains the final source of truth for authorization, validation, transitions, and tenant isolation. Drift/SQLite is a durable read cache, never an authorization source or a PostgreSQL mirror. UI accesses data through repositories coordinating remote and local data sources.

Default future feature behavior is stale-while-revalidate: show scoped cache, attempt HTTP refresh, atomically replace valid local data, and retain old data on network/parse/write failure. HTTP success/failure is authoritative; no connectivity plugin gates requests. Server-state mutations remain online-only and never fake success.

## Scope and lifecycle

Each school record key includes `localUserKey`, `membershipId`, `academicYearKey`, resource type/id. Context switching first binds to the new scope; it never displays the previous membership and does not delete other context caches. Historical cache carries `isHistorical=true` and is read-only metadata.

One application-scoped `AppDatabase` opens `school_saas_mobile_cache.sqlite` through `drift_flutter` in the platform application-private documents directory on Android and iOS. There are no hardcoded platform paths. Schema version starts at 1 with an explicit additive migration hook and no destructive production fallback.

## Security and logout

Passwords, JWTs, authorization headers, secrets, and attachment bytes never enter SQLite. JWTs remain in `flutter_secure_storage`. Explicit logout and terminal session expiry purge the current user's sensitive cache; font preference remains. Closing the app does not purge cache. Another local user cannot query the previous user's scope.

### Local data at rest security decision

The database is not additionally encrypted in 5B.0. The selected compatible Drift stack provides app-sandboxed private storage on Android and iOS, while credentials remain separately encrypted by secure storage and user cache is purged on logout/session expiry. A maintained, SDK-compatible encryption stack and key lifecycle/threat-model review are required before making database encryption mandatory for production; adopting a deprecated encryption plugin would increase risk.

## Attachments and deferred writes

Future attachment metadata may live in DB; bytes belong only in app-private file cache, never Gallery/Downloads or SQLite. Size/LRU cleanup policy is deferred. Homework text/file-reference drafts may be designed later, but final submit remains online-only.

Deferred until a backend idempotency contract exists: Offline Outbox, write synchronization, automatic retries, conflict resolution, and idempotency keys. Biometric/PIN and long-lived offline unlock are also deferred.

## Cross-platform contract

Android and iOS share this implementation, cache semantics, tenant isolation, and logout purge behavior. Dependencies must provide Android and iOS implementations. iOS build/simulator/device verification is pending macOS with Xcode and is not replaced by an Android-only architecture.

## Timetable implementation — Sprint 5B.1

Schema v2 adds `CachedTimetableDatasets`, keyed by local user, membership, academic year, and dataset (`today`, `week`, `current`, `next`). The repository reads all four cached datasets first, then refreshes the bounded production endpoints and transactionally replaces only fully parsed payloads. Current/Next are never derived locally. Network failure preserves and displays the previous cache with offline/last-updated UI; no cache yields a controlled error.

## Homework implementation — Sprint 5B.2

Schema v3 additively introduces `CachedHomeworkItems` and `LocalHomeworkDrafts`. Both use local user + membership + academic year + homework ID keys, so context/user switches cannot expose another scope. Cached Homework JSON contains server fields, permission hints, submission state, and attachment metadata only; it never contains attachment bytes, credentials, or authorization data.

The Homework repository reads list/detail locally first, attempts the real API, and replaces only parsed scoped records. A Local Draft stores answer text, a device-only personal note, and optional app-private local file references. It survives tab changes, app restart, and network failure, but explicit logout/session purge deletes it. Final submit is online-only: create or reuse the server draft, PATCH the answer, request final submit, refresh remote state, and only then delete the Local Draft. Failure never queues, fakes success, or deletes the draft.

Homework attachments download online to the cross-platform application documents directory through `path_provider`; SQLite stores metadata only. Opening/viewer integration and file-cache size/LRU management remain deferred rather than introducing a large attachment engine.
