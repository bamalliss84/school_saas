# Backend UX Contract Rebuild Report

## Decision

**BACKEND UX CONTRACT READY — SAFE FOR FLUTTER DESIGN**

## Baseline

- Commit: `565f672 Sprint 4.7: add timetable daily schedule and integrity hardening`.
- Scope: analysis/documentation only. No production code, model, API, service, migration, tests, staging, commit, or push.

## Files reviewed

- Routing/schema: `backend/config/api_urls.py`, schema annotations and serializers.
- Context/auth/permissions/errors: `context.py`, `context_views.py`, `identity_views.py`, `permissions.py`, `api_exceptions.py`, auth/current-user serializers/views.
- Domain models: SchoolMembership, StudentEnrollment, TeacherAssignment, Attendance, Exam/ExamResult/Log, Homework/Submission, Notification, Conversation/Message, Announcement, Timetable models.
- Production flows: attendance selectors/views/serializers/service; exam selectors/views/serializers/result service; homework selectors/views/serializers/services; messaging/notification/announcement services and views; timetable selectors/serializers/views/service.
- Passing behavioral evidence: Sprint 4D/4B/4C/4.6/4.7 test modules, especially timetable API/model tests and accepted 609-test baseline.
- Existing architecture/timetable docs were used only where consistent with code. The prior Backend UX files were not treated as truth.

## Roles analyzed

Student، Parent، Teacher، School Admin، Super Admin. Super Admin was kept separate from the future Platform Owner concept.

## Workflows analyzed

- JWT/session and Active Context selection/default/history/unavailable states.
- Student/parent identity and academic history.
- Timetable read/admin grid and daily attendance integration.
- Attendance daily records/bulk/reports/summaries.
- Homework and HomeworkSubmission independent workflows plus derived completion.
- Exam/result grading, approval and publication separation.
- Private messaging, attachments, read markers, School Support and Teacher Broadcast.
- Membership-scoped notifications and announcements lifecycle/targeting/inquiry.

## Timetable status

Timetable is `SUPPORTED_NOW`, not planned. Teacher Today/Week/Current/Next, Student schedule, linked Parent schedule, and Admin Config/Periods/Grid/Bulk/Validate/Copy/Assignment Options are present. The contract preserves `TeacherAssignment = WHO/WHAT/WHOM` and `TimetableEntry = WHEN/WHERE`.

Sprint 4.7.1 semantics were confirmed: attendance shortcut is Daily Attendance; statuses are `not_recorded`, `partial`, `recorded`; `attendance_expected_count` is exposed; only an eligible owning Teacher can receive `can_take_attendance=true`. Student/Parent/Admin/historical receive false.

## Active Context findings

- Canonical authority is `request.active_membership/school/role/academic_year`.
- Multiple active memberships without a header produce `409 context_required`.
- Active = read/write subject to role; historical = read-only plus personal communication read markers; suspended/ended/inactive school = unavailable.
- Timetable, messaging, notifications and announcements use canonical context directly.
- School data must never be merged across selected contexts in UI.

## Historical findings

The rebuilt contract lists concrete visible and hidden behavior per role. Academic history and timetable are explicit. Historical student/parent Homework reads are supported and mutation flags are false. Delivered announcements, notifications and conversations remain readable in their membership context, and personal read markers remain allowed. Academic/content creation, submissions, attendance, grading, workflow actions, broadcasts, new messages/support and administrative mutations must be hidden.

## Legacy findings

Attendance, exams/results, Homework and some original identity endpoints still consult `request.user.school/role/academic_year` internally. Active Context authentication projects the selected membership into those fields for the request only and restores it without saving. These features are therefore classified `SUPPORTED_WITH_LEGACY_COMPATIBILITY`, not as gaps and not as canonical UX concepts. Removing this dependency remains technical debt.

## Parent UI compatibility

Backend supports linked children, children across school memberships, child school/history views, timetable, attendance, homework monitoring, published results, notifications, private teacher/homework conversations, School Support and announcements. Parent cannot edit academic records or combine schools in one tenant dataset. Compatible with the intended Parent UI direction.

No repository file named `PARENT UI FREEZE V1` was available at this baseline; compatibility was evaluated against the Parent checklist supplied with this task and current production APIs.

## Student UI compatibility

Backend supports current context/profile/history, timetable, complete HomeworkSubmission lifecycle, published results, attendance, notifications, private messages/homework discussion, support, announcements and historical read-only mode. Compatible with the intended Student UI direction.

No repository file named `STUDENT UI FREEZE V1` was available at this baseline; compatibility was evaluated against the Student checklist supplied with this task and current production APIs.

## Teacher UI compatibility

Backend supports multi-school switching, Today/Current/Next/Week, attendance, assignment students, Homework/submission grading/return, Exams/bulk results/submit/correction, messaging tied to assignment/student, Homework discussion, Teacher Broadcast, notifications, announcements and historical reads. Approval/rejection/reopen/publication and Timetable Grid editing are Admin-only and must not appear in Teacher UI.

## Unsupported design assumptions

- Super Admin as Platform Owner or subscription operator.
- Group chat, free recipient search, multi-guardian conversation, or Teacher Broadcast as chat.
- Per-period attendance.
- Teacher approval/publication of results.
- Parent/student academic writes.
- Cross-school combined data screens or disclosure of another school's timetable.
- Historical write controls beyond personal read markers.
- Timetable calendar exceptions, versioned bell times, structured rooms or cross-school warning as already supported.

## Blockers for Flutter

No blocker for Flutter foundation or Student/Parent/Teacher UX design under this contract. Flutter must implement context selection, 409 handling, historical read-only state, role/state-driven action hiding, and the standard error envelope before feature screens are considered safe.

The future School Admin customer portal, Platform Control Plane, subscriptions, onboarding and import center are outside the initial mobile-role contract and remain gaps.

## Deferred items

- Platform Owner/Control Plane and subscriptions.
- School Admin Web Portal.
- Onboarding wizard and validated Excel Import Center.
- Full legacy context migration/removal.
- Timetable bell-time versioning, calendar exceptions, privacy-safe cross-school teacher warning and optional Room model/conflicts.

## Final finding

The rebuilt `BACKEND_UX_CONTRACT_V1.md` reflects current production behavior after Timetable hardening, separates current support from legacy compatibility and planned gaps, and is suitable as the functional source of truth for Flutter design.
