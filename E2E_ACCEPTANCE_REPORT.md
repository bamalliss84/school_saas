# Sprint 4.6 E2E Acceptance Report

## 1. Baseline commit

`503f7b6 Sprint 4C-4.5: finalize announcements and freeze backend architecture`. The initial worktree was clean.

## 2. Files added

Management package/command, `test_sprint46_demo_seed.py`, `test_sprint46_e2e_acceptance.py`, `SPRINT_4_6.md`, `DEMO_DATA.md`, and this report.

## 3. Production files modified

- `core/models.py`: fixed teacher code increment and membership-aware Exam/Homework creator validation with legacy fallback.
- README, Roadmap, Project Context, and progress report: Sprint 4.6 documentation only.

No model field/relationship/API URL was changed and no migration was created.

## 4. Seeder architecture

`seed_demo_school` is atomic, deterministic and idempotent. It uses exact `DEMO_NOOR`/`DEMO_FUTURE` school codes and `demo_` usernames. It has no API endpoint. Non-DEBUG execution requires explicit `--allow-non-debug`; reset is domain-ordered and deletes only marked Demo records.

## 5. Demo schools

Two active schools, two years each, terms, Grades 6/7, Sections A/B, four subjects, class-subject mappings and three exam types per school.

## 6. Demo users

Super admin, two school admins, two single-school teachers, one multi-school teacher, two parents, twenty regular students and one transferred student. Credentials are synthetic and documented only as development credentials.

## 7. Membership matrix

Single-school users have active default memberships. `demo_teacher_multi` has active teacher memberships in both schools. `demo_student_transferred` has historical School A and active/current School B. `demo_parent_multi` has current B and historical A contexts.

## 8. Student transfer scenario

One account and Student record, old non-current School A enrollment and current School B enrollment. Old attendance and announcement receipt remain in A; current notification and enrollment are in B. No operational data was copied.

## 9. Multi-school teacher scenario

School A Grade 7/A Science and School B Grade 6/B Mathematics assignments are distinct. Login once, context listing returns two contexts, no header returns 409, and switching headers returns disjoint assignment sets.

## 10. Parent scenario

Parent A sees exactly two linked children. An unrelated same-school Student detail returns 404. Parent result feed contains published results only.

## 11. Attendance result

22 deterministic rows cover present/absent/late/excused and both current/historical enrollments. Existing API suite verifies teacher assignment, admin, parent/student visibility, bulk atomicity and tenant IDOR.

## 12. Exam/result result

Demo includes exam types and an approved/published School A quiz result. API E2E verifies parent/student read behavior; full regression verifies draft/submitted/rejected/approved-unpublished/published policies.

## 13. Approval result

Teacher submit and admin approve authorization/workflow tests pass in the full suite.

## 14. Publication result

Student/parent visibility remains approval plus explicit publication only. Reopen/unpublish metadata and audit regressions pass.

## 15. Homework result

Independent published homework exists in both schools; School A includes a graded submission. E2E reads and full workflow tests for publish/submit/grade/return/derived completion pass.

## 16. Notifications result

Synthetic and workflow notifications remain membership-scoped. E2E proves the transferred user's current/historical feeds are disjoint and personal read/read-all works.

## 17. Messaging result

Demo School Support conversation/message uses a same-school membership participant. Full API suite verifies teacher-student, one-parent privacy, reply/read, attachments, lifecycle and forbidden peer/cross-school messaging.

## 18. School Inbox result

Full API E2E regression verifies creation, assignment, reply, in-progress/resolve/reopen policy, audit and School B denial of School A objects.

## 19. Announcements result

Independent School A school-wide and School B student-role announcements have membership receipts. Student unread/read E2E passes; full suite covers all targeting modes, summary, close/archive and notification behavior.

## 20. Inquiry result

Full Sprint 4C API tests verify assignment inquiry routing, School Support routing and denial for non-recipients.

## 21. Historical context result

Transferred Student historical A context reads context/history/results/homework/announcements. Attendance create, conversation start and PATCH are rejected with 403.

## 22. Context switching result

Multi-school teacher: contexts=2, missing header=409, selected A/B assignments are disjoint. Live HTTP repeated login/contexts and selected-context resource feeds successfully.

## 23. IDOR attack matrix

Direct foreign IDs are covered across the combined Demo E2E and full security suite: Student, enrollment/history, assignment, Attendance, Exam, ExamResult, Homework, submission, Notification, Conversation, Message, Announcement, receipt-derived visibility and attachments. Foreign detail/actions return 404/403/400 according to the frozen contract; no cross-school access succeeded.

## 24. Role matrix

| Role | Verified primary access | Forbidden/isolation evidence |
|---|---|---|
| Super Admin | login/context and administrative workflows | school-context rules retained |
| School Admin | school academic/workflow resources | foreign assignment/object rejected |
| Teacher | assignments/students/homework/messages | unassigned and foreign objects hidden |
| Parent | linked children/results/homework | unrelated Student 404 |
| Student | own profile/results/homework/announcements | peer/foreign and historical writes denied |

## 25. Auth tests

Login, wrong password, refresh, logout, refresh after blacklist, inactive user/school/membership and old-token membership state behavior pass.

## 26. API error tests

Representative 400, 401, 403, 404, 405, 409, 415 and throttled 429 envelopes are covered by Sprint 4.6 plus existing infrastructure tests. No envelope change was made.

## 27. Database consistency checks

Zero duplicate current enrollments, invalid default memberships, cross-school conversation participants, invalid published results, cross-school announcement receipts, notification membership mismatches or inconsistent notification read metadata.

## 28. Seeder idempotency

Run 1 and Run 2 both report 2 schools, 21 students and 22 attendance rows; automated snapshots are identical.

## 29. Seeder reset result

`--reset-demo` removes and rebuilds the same shape while preserving an unrelated control school. Protected workflow rows are removed in domain-safe order.

## 30. Full test count

590/590 PASS on Windows/PostgreSQL. Baseline was 577.

## 31. Coverage

`9950 statements, 710 missing, 93%` — PASS.

## 32. Ruff

`All checks passed!` for `backend/core` and `backend/config`.

## 33. Django check

`System check identified no issues (0 silenced)`.

## 34. Deploy warnings

Only the three documented development warnings: HSTS seconds, SSL redirect and development secret key.

## 35. Migrations

`No changes detected`; no pending migrations; applied schema remains through core 0023. No Sprint 4.6 migration.

## 36. OpenAPI

Official `spectacular --validate` completed with zero errors/warnings. No seed endpoint exists.

## 37. Server smoke

Development server used the real Demo dataset. Login=200, contexts=2, missing header=409, and selected-context me/assignments/students/homework/notifications/conversations/announcements all returned 200.

## 38. runserver count

Zero after explicit shutdown.

## 39. Performance observations

The approximately 21-student/two-school dataset produced responsive list requests in local smoke. Existing query construction uses related loading/scoped queries; no obvious N+1 or latency escalation was observed. No speculative performance change was made.

## 40. Bugs discovered

1. Teacher employee code generation parsed `T00001` directly as an integer and repeated the first code.
2. Exam/Homework model validation authorized creators from legacy `User.school`, blocking a multi-school teacher in School B.
3. Initial reset ordering encountered protected announcement/conversation memberships and published-result SET_NULL constraints.

## 41. Bugs fixed

Teacher suffix parsing now removes only the `T` prefix and has a regression test. Exam/Homework validate an active teacher/admin membership when memberships exist, retaining legacy fallback only for unmigrated users. Reset deletes marked protected/constrained workflow rows before marked schools. All fixes have targeted and full regression coverage.

## 42. Remaining risks

Production TLS/secrets/storage/providers remain deployment-only work. Demo reset deliberately knows the currently seeded protected domains; future Demo entities with new PROTECT relations must be added to its ordered reset. Older explicitly documented legacy request-context reads remain separate migration debt.

## 43. Final decision

**SPRINT 4.6 E2E ACCEPTED — READY FOR FLUTTER**

Flutter was not started. No git add, commit or push was performed.
