# Phase 0 — Acceptance Fix Pack B

Baseline: `1f77e19` (Fix Pack A).

## Scope
Only the three acceptance findings were changed:

1. Appearance/font application: keep the current tab/router state and apply the selected bundled font to all customized text styles.
2. Offline banner: use the session-level banner as the single source of truth; remove feature-local duplicate/flash banners.
3. Stale membership: await 403 context revalidation, invalidate a no-longer-usable current membership before surfacing the error, and use the Arabic unavailable-school-context wording. Ordinary 403 permissions remain ordinary permissions.

## Offline security boundary
A device that is genuinely offline cannot know that an administrator changed a membership on the server after the last successful validation. Cached read-only data therefore remains available using the last locally validated context while offline. As soon as connectivity returns and an API request receives 403, the client revalidates the membership before continuing and invalidates/replaces the stale context when necessary.

No Homework/Results business workflow, score semantics, Nano design, or new feature was changed.
