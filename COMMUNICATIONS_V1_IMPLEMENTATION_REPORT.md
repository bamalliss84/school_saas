# Communications V1 — RC Implementation Report

Date: 2026-08-21

Implemented in this RC:
- Notifications list, unread filter, read/read-all, badge in student header.
- Notification action dispatcher for homework/result/conversation/school-support routes with safe fallback.
- Announcements list/detail expansion, read state, attachment metadata count.
- Conversations list, unread count, detail/messages, send gating, historical/offline read-only behavior.
- Communications snapshot cache scoped by user/membership/academic-year using existing CachedContexts (no Drift schema migration).
- Per-conversation message cache and transport-only offline fallback.
- School Support create form using backend-supported categories.
- Demo communications data for demo_student_a_01.
- Design references remain under design/student_v1/.

Not marked CLOSED yet:
- Flutter analyze/test must be run on the user's Flutter SDK after installing this RC.
- Announcement inquiry button and binary attachment upload/open UX are not yet closed.
- School Support attachment two-step UX is not yet closed.
- Full 320x480 / 150% / offline-empty visual regression is pending device/test execution.

Backend models/APIs were not rebuilt.
