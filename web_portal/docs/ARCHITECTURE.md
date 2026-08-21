# School Admin Web Portal — Architecture Document (W1)

**Version:** 1.0.0  
**Phase:** W1 (Functional Web Foundation)  
**Author:** Antigravity Agent  
**Status:** Active  

---

## 1. Architectural Overview

The **School Admin Web Portal** is an enterprise-grade Single Page Application (SPA) designed to empower School Administrators to manage academic operations, timetable configurations, attendance oversight, homework monitoring, exam results approvals, communications, and reporting across multi-school tenant boundaries.

```
+-----------------------------------------------------------------------------------+
|                              School Admin Web Portal                              |
+-----------------------------------------------------------------------------------+
|  AppShell Layout (RTL Arabic First)                                               |
|  +---------------------------+-------------------------------------------------+  |
|  | Sidebar                   | Topbar: Active School & Year Badge | User Menu  |  |
|  | - Dashboard               +-------------------------------------------------+  |
|  | - Academic Setup (W4)     | Historical Read-Only Banner (if applicable)     |  |
|  | - People Mgmt (W5)        +-------------------------------------------------+  |
|  | - Timetable (W7)          | Main View Outlet (Protected by Route & Context) |  |
|  | - Attendance (W8)         |                                                 |  |
|  | - Homework (W9)           |   [ Dashboard / Module Placeholder ]            |  |
|  | - Exams & Results (W10)   |                                                 |  |
|  | - Communications (W11)    |                                                 |  |
|  | - Data Import (W6)        |                                                 |  |
|  | - Settings (W14)          |                                                 |  |
|  +---------------------------+-------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
|  Core Services & Security Layer                                                   |
|  - apiClient (Axios/Fetch wrapper: JWT Bearer, X-School-Membership-ID)            |
|  - Single-Flight Refresh Mutex & Replay Protection                               |
|  - Error Envelope Normalizer ({ success: false, message, errors })                |
|  - AuthContext & Role Guards (School Admin / Super Admin verification)            |
+-----------------------------------------------------------------------------------+
                                         |
                                         | Vite Dev Proxy (/api/v1/)
                                         v
+-----------------------------------------------------------------------------------+
|                            Django REST Framework Backend                          |
+-----------------------------------------------------------------------------------+
```

---

## 2. Authentication & Session Lifecycle

### 2.1 Login Flow
1. User submits credentials at `/login` via `LoginPage`.
2. `authService.login()` posts to `POST /api/v1/auth/login/`.
3. Backend returns JWT `access` and `refresh` tokens, user identity, `default_membership_id`, and `has_multiple_contexts`.
4. Client stores tokens and queries `GET /api/v1/auth/contexts/` to retrieve available `SchoolMembership` instances.
5. If the user belongs to multiple active schools without a default, `ContextSelectorModal` is displayed or user is routed to `/select-context`.
6. Upon active context confirmation, `X-School-Membership-ID` is registered in `apiClient` and user is routed to `/dashboard`.

### 2.2 Token Refresh & Expiry Handling
- API requests encountering a `401 Unauthorized` automatically trigger the single-flight refresh mutex via `POST /api/v1/auth/refresh/`.
- If the refresh succeeds, all pending requests are replayed with the new access token.
- If refresh fails (token blacklisted/expired), auth state is cleared, and user is redirected to `/login`.

### 2.3 409 `context_required` Handling
- When the backend returns a `409 Conflict` with `errors.code === 'context_required'`, `apiClient` invokes `onContextRequiredCallback`.
- `AuthContext` catches this event and opens `ContextSelectorModal` to allow the user to select an unambiguous active school context without disrupting application state.

---

## 3. Multi-Tenant Context & Historical Mode

### 3.1 Tenant Scope
- The client injects `X-School-Membership-ID: <activeMembershipId>` on all protected API requests.
- No client-supplied school ID in query params or request bodies is trusted to establish tenant scope.

### 3.2 Historical Context (Read-Only Mode)
- When `activeMembership.status === 'historical'` or `activeMembership.access_mode === 'read_only'`, the portal activates Historical Mode:
  1. `HistoricalBanner` displays a persistent, prominent warning at the top of the interface.
  2. `isReadOnly` is set to `true` across `AuthContext`.
  3. All mutation buttons (create, edit, delete, publish, approve) are disabled/hidden across the UI.
  4. Backend enforces 403 PermissionDenied on non-safe HTTP methods.

### 3.3 Unavailable Contexts
- Memberships with status `suspended`, `ended`, or inactive schools are disabled in the context selector with an explicit warning badge and cannot be selected.

---

## 4. Routing & Guard Hierarchy

```
/login (Public)
/unauthorized (Public feedback for non-admin accounts)

/ (Protected by AuthGuard)
  ├── /select-context (Protected by SchoolAdminGuard)
  └── / (Protected by SchoolAdminGuard + ContextGuard)
        └── AppShell (Layout)
              ├── /dashboard (Placeholder Dashboard)
              ├── /academic (Phase W4)
              ├── /people (Phase W5)
              ├── /timetable (Phase W7)
              ├── /attendance (Phase W8)
              ├── /homework (Phase W9)
              ├── /exams (Phase W10)
              ├── /communications (Phase W11)
              ├── /data (Phase W6)
              ├── /reports (Phase W12)
              └── /settings (Phase W14)
```

---

## 5. Design System Tokens & RTL First Principles

- **RTL Support:** `dir="rtl"` set natively on `<html>` with Arabic typography (Cairo & Tajawal).
- **Color Tokens:**
  - Primary (Brand Blue): `var(--primary-600)` (`#2563eb`)
  - Slate (Neutrals): `var(--neutral-50)` to `var(--neutral-950)`
  - Emerald (Success): `var(--success-600)` (`#059669`)
  - Amber (Warning / Historical): `var(--warning-500)` (`#f59e0b`)
  - Rose (Danger / Error): `var(--danger-600)` (`#e11d48`)
- **Responsive Layout:** Desktop-first (1400px container max-width) with collapsible sidebar (260px expanded, 72px collapsed) and tablet adaptability.
