# Flutter Sprint 5A Acceptance Report

## Baseline and scope

- Backend baseline: `565f672`.
- Backend production logic and migrations: unchanged.
- Existing untracked `BACKEND_UX_CONTRACT_V1.md` and `BACKEND_UX_CONTRACT_REPORT.md`: preserved outside this work.
- No Student/Parent/Teacher feature implementation beyond approved placeholder shells.

## Verification evidence

| Check | Result |
|---|---|
| `flutter doctor` | PASS; no issues found |
| `flutter pub get` | PASS; got dependencies and exited successfully |
| `dart format lib test` | PASS; 16 files formatted |
| `flutter analyze` | PASS; no issues |
| `flutter test` | PASS; 7/7 |
| Real Demo login | PASS (`demo_teacher_multi`) |
| Context list | PASS; 2 contexts |
| Membership-scoped `auth/me` | PASS using `X-School-Membership-ID` |
| Temporary server shutdown | PASS; `RUNSERVER_COUNT=0` |
| Backend full suite / coverage | Not rerun by instruction |

The previous rejection was environment-only: Windows symlink support/Developer Mode was disabled. Developer Mode has now been enabled and the blocked Flutter checks pass. Available package updates are not an acceptance failure; dependency versions remain on the current stable set and were not updated.

The first live smoke exposed two client contract mismatches (header suffix and singular default-context route). Both were corrected against Django routes and the frozen contracts, then the live smoke passed.

## Security and tenancy

Tokens use `flutter_secure_storage`; no secrets are committed. Tenant authorization uses membership ID only. Historical mode reports `canWrite=false`; unsupported mobile roles cannot enter feature shells. Refresh is single-flight and retry-limited.

## Decision

**SPRINT 5A FLUTTER FOUNDATION ACCEPTED — READY FOR STUDENT APP**

The successful Real Demo API smoke was not rerun because the code has not changed since that smoke. Its accepted evidence remains: `demo_teacher_multi` login PASS, 2 contexts PASS, membership-scoped `auth/me` with `X-School-Membership-ID` PASS, and `RUNSERVER_COUNT=0`.

No git add, commit, or push was performed.
