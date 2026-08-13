# Mobile Architecture — Sprint 5A

## Boundaries

- `core/`: configuration, Dio client, error mapping, secure session storage, typed shared models.
- `features/authentication/`: login/logout and current-user repository.
- `features/school_context/`: context loading and explicit default selection.
- `app/session/`: Riverpod state machine and routing decisions.
- `app/app.dart`: Arabic RTL shell and role-specific placeholder navigation.

`SchoolMembership` is the authorization identity. The client always sends the selected membership through `X-School-Membership-ID`; legacy user school/role fields are never authorization inputs. Switching context replaces the tenant session state. Future tenant repositories must invalidate their providers/caches on the same transition.

## Session flow

Login stores JWT tokens in secure storage, then loads `/auth/contexts/`. One usable context is selected automatically; multiple contexts open the selector. Historical contexts are read-only and visibly bannered. Student, Parent, and Teacher enter their placeholder shells; admin roles are unavailable on mobile.

The Dio interceptor refreshes JWT through a single shared in-flight operation, retries the failed request once, clears credentials on refresh failure, and maps the standard HTTP statuses. A 409 invokes the context-required boundary. Network failures preserve a user-readable retry path and never bypass server authorization.

## Deferred

No Student, Parent, Teacher, offline cache, notification provider, or production feature logic is part of Sprint 5A. Those belong to subsequent feature sprints.
