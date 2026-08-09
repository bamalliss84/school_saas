# Active Context Migration Report

## Canonical state

New context-aware code authorizes with `active_membership`, `active_school`, `active_role`, and `active_academic_year`. Sprint 4C announcements, notifications, messaging, and identity/context endpoints follow this rule.

## Usage classification

- `SAFE_LEGACY_COMPATIBILITY`: `core/context.py` reads persisted legacy fields to bootstrap a membership for old users and temporarily projects the selected membership onto the in-memory user object. The original values are restored; the mutation is never saved.
- `MIGRATION_OR_ADMIN_ONLY`: Django Admin uses persisted role/school fields as its separate staff authorization boundary and applies tenant queryset/FK scoping.
- `DEFERRED`: older `selectors.py`, `exam_selectors.py`, `homework_selectors.py`, `views.py`, related serializers, and older exam/homework services read the request-local projected user fields. They are covered by context-switch, role-source, historical-write, and cross-school tests, but should be converted to explicit context arguments in a dedicated compatibility-removal sprint.
- `MUST_FIX_NOW`: none remaining after this acceptance pass.
- `DEAD_CODE`: none asserted without evidence.

## Security evidence

The suite covers missing context (409), foreign membership (404), suspended/ended/inactive contexts (403), historical writes (403), role/school selection from membership, cross-school object isolation, and request-local restoration of legacy fields. All 577 tests passed on PostgreSQL.
