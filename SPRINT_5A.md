# Sprint 5A — Flutter Foundation, Authentication & Active Context

## Scope delivered

- Flutter application under `mobile_app/` with feature-first boundaries.
- Riverpod session state machine and GoRouter route selection.
- Dio API client with secure tokens, membership header, single-flight refresh, one retry, and typed failure mapping.
- Real login, current user, contexts, default-context, and logout repositories.
- Active-context auto-selection, multi-context picker, historical read-only mode, and unsupported admin state.
- Arabic RTL theme, reusable historical banner, and Student/Parent/Teacher placeholder navigation shells.
- Unit and widget coverage for the Sprint 5A contracts.

## Out of scope

Feature screens, backend production changes, offline database/cache, push providers, Flutter UI freezes, and any deployment configuration.

## Acceptance

- Dart format: PASS.
- Flutter doctor: PASS, no issues found.
- Flutter pub get: PASS, dependencies resolved successfully.
- Flutter analyze: PASS, no issues.
- Flutter tests: 7/7 PASS.
- Real Demo API smoke: login, two contexts, membership-scoped `auth/me`: PASS.
- Temporary Django server stopped: `RUNSERVER_COUNT=0`.

The previous rejection was environment-only: Windows symlink support/Developer Mode was disabled. That host issue is resolved and all required Flutter checks now pass. Available package updates are not a failure; current stable dependency versions were preserved without updates.

The Real Demo API smoke was not repeated because the code has not changed since its successful run: `demo_teacher_multi` login PASS, 2 contexts PASS, `X-School-Membership-ID` scoped `auth/me` PASS, and `RUNSERVER_COUNT=0`.

## Final decision

**SPRINT 5A FLUTTER FOUNDATION ACCEPTED — READY FOR STUDENT APP**
