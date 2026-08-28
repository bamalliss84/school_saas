# Latest Acceptance Report

## M1.4 — Student App Final Regression

**Decision: M1.4 CLOSED / ✅ SUPERVISOR ACCEPTED. STUDENT MOBILE V1 OFFICIALLY CLOSED / DONE — READY FOR SCHOOL PILOT.**

- Baseline: `365d64c65e7813346139e2d72662c17da25ed701` on `agent/codex-mobile`; M1.2 and M1.3 remain closed/accepted. Existing unstaged Results and generated registrant changes were preserved and excluded.
- Reviewed the integrated Student journey across authentication/session restoration/logout, context selection, Home/Timetable/Attendance, Homework, Results, Communications/School Support, and More/Profile/History/Appearance/Help/About.
- Multi-context: the accepted `demo_student_a_01` current Noor 2025/2026 and historical Future 2024/2025 contexts remain selected through membership IDs. Feature cache scope remains local user + membership + academic year; Student Shell is keyed by membership and does not reuse the prior context UI.
- Offline/recovery: no connectivity-only online shortcut was introduced. Transport failures continue to drive cached/offline behavior; only a successful real API response invokes connection restoration. Offline mutations remain blocked by the accepted feature rules.
- Historical: shared historical state/banner remains authoritative. Homework submission/editing, Support creation/reply, announcement inquiry, and other mutations remain unavailable; read-only domain views remain accessible.
- Regression found/fixed: Student Shell Android system Back did not treat open Homework detail, Result detail, or Message/Support conversation as nested destinations, and Attendance detail Back skipped its list. The shell now closes the active feature detail first, matching each existing explicit Back action, without changing routing, business state, APIs, caches, or permissions.
- Results runtime recheck regression: the Results provider is eagerly loaded and tab selection can request a refresh while that load is still active. The controller previously emitted cached rows before refresh and allowed concurrent load completions to replace the same `ResultsReady` state, which could flash older same-scope grades and clear/override a just-selected detail. Results loads are now coalesced, online initial load remains a proper loading state until fresh data arrives, exact-scope cache is used only as an offline fallback, and refresh completion preserves the current filters/detail selection.
- Results cache audit: the Drift primary key and provider family both use local user + membership + academic year; no cross-context key defect or Backend contract defect was found.
- Supervisor runtime recheck: PASS. No grade-value flashing; Result detail opens on the first tap; Back returns to the same list state; current/historical contexts remain isolated; offline exact-scope cache and online recovery are accepted.
- Static responsive review retained accepted bounded/scrollable layouts for RTL, narrow widths, 150% text, keyboard-safe Support, fixed bottom navigation, and the accepted M1.3 wrapping weekday selector. No additional layout defect was proven statically.
- Final staged diff check initially found two Markdown trailing spaces in the roadmap status line; they were removed and the check was rerun successfully.
- Backend changed: NO. Migration: NO. Flutter/Dart analyze and tests: NOT RUN by explicit Supervisor restriction. Push: NOT RUN.
- Next official Mobile milestone: Teacher App V1 / M2. The Student V1 completion gate is satisfied, so M2 is unblocked but has not started.

## M1.3 — Student Timetable UI Closure

**Decision: M1.3 CLOSED / ✅ SUPERVISOR ACCEPTED.**

- Baseline: `e92c28e02a2645a3dade83365d600a8dacfef1d2` on `agent/codex-mobile`; the existing accepted Timetable presentation work was retained and extended. Unrelated Results and generated registrant changes remain untouched.
- Existing production `timetable/today/`, `week/`, `current/`, and `next/` feeds and the existing scoped Drift cache remain unchanged; no Backend or migration change was needed.
- Today: entries and periods are deterministically ordered by period sequence/id. Only Backend-authoritative Current/Next IDs receive the corresponding visual emphasis; finished entries remain restrained.
- Week: days are ordered by date, the actual Today date is selected/identified, empty selected days are explicit, and the horizontally scrolling day selector remains compact.
- Empty states distinguish an unconfigured timetable, a configured day with no lessons, no current lesson, and no next lesson. Transport/API failures keep the existing controlled error behavior; no unsupported publication state was invented because the Timetable contract has no publication field.
- Offline/cache: existing user + membership + academic-year scoping is preserved. Focused coverage verifies cached fallback and that a successful refresh clears controller offline state.
- Historical: the shared shell banner remains authoritative; the full timetable also identifies the previous-year view as view-only and exposes no mutation controls.
- Navigation: the full timetable has an explicit Back action, and Student Shell intercepts Android Back for Timetable and other existing nested destinations before allowing the shell to exit.
- Responsive: long Arabic subject, teacher, classroom, section, period, and time metadata use bounded flexible layout; 320×480 at 150% text scale has focused no-overflow coverage.
- Responsive runtime fix: the fixed-height horizontal weekday strip was replaced by an RTL wrapping selector so every full Arabic day chip and selected/check state remains visible and reachable without shrinking labels.
- Focused Timetable tests: 17 PASS, including exact 320×480/150% RTL viewport-bound checks for all seven weekday chips. Full `flutter test --no-pub`: PASS — 103 tests.
- `dart format`: PASS on the four M1.3 Dart files. `flutter analyze --no-pub`: PASS — no issues found.
- Supervisor Android Medium Phone runtime acceptance: PASS. Today/Week presentation, RTL wrapping, selected current day, and the responsive weekday-selector recheck have no visible clipping or overflow.
- Backend changed: NO. Migration: NO. Commit/push: NOT RUN.

## M1.2 — Student More / Profile + Context UX

**Decision: M1.2 CLOSED / ✅ SUPERVISOR ACCEPTED.**

- Baseline: `e8884ea` on `agent/codex-mobile`; unrelated Results/Timetable and generated registrant working-tree changes were preserved and excluded.
- More: Nano-aligned Student account hub with Profile, conditional multi-context action, Academic History, Appearance, Help, About, and existing Logout.
- Profile: real `GET students/me/profile/` identity fields only; read-only, loading/error/retry/offline-cache states, long-value safety, and historical context labeling without leaking the current enrollment into another selected school.
- Context: canonical `auth/contexts/` session list only. Switching uses the existing default-context contract and restores the previous stored membership/session when completion fails. Offline switching is disabled; single-context users do not see a redundant switch action.
- History and schools: real `students/me/academic-history/?school_membership_id=<active membership>` and `students/me/schools/`; the latter supports presentation only and does not duplicate context authorization.
- Cache: existing `CachedContexts`, scoped by user + membership + academic year with resource `student_more_profile_v1`; no Drift schema or migration change.
- Navigation: nested More destinations have explicit back actions; Android system Back returns to More before leaving Student Shell. Help routes to the accepted Communications tab instead of creating another support system.
- Appearance/font persistence and current logout/session purge behavior are preserved.
- Focused M1.2 tests: 15 PASS, covering endpoint parsing/queries, scoped cache isolation, single/multiple context UX, successful/failed/offline switching, rollback, historical mode, history empty/data, Help/About/Logout/Back, long Arabic content, and 320×480 at 150%.
- `flutter analyze --no-pub`: PASS — no issues found.
- `flutter test --no-pub`: PASS — 93 tests.
- Supervisor Android Emulator runtime acceptance: PASS. Multi-context selector, current-context identification, historical selection, topbar/context refresh after switching, historical banner, read-only enforcement, and switching behavior were accepted.
- Backend changed: NO. Migration: NO.

## Mobile Student Communications — offline recovery and support entry layout

**Decision: STUDENT COMMUNICATIONS V1 / SCHOOL SUPPORT CLOSED — ✅ SUPERVISOR ACCEPTED.**

- Root cause: Communications had no independent Internet-status source. A transport failure to the Backend marked both the session and cached Communications snapshot offline. The emulator network is currently Android `VALIDATED`, and `10.0.2.2:8000` is reachable, so the visible banner was stale state from an earlier Backend transport failure rather than current Internet loss.
- Recovery: when a real successful API response changes the session from offline to online, Student Shell now refreshes Communications. Only a successful Communications refresh replaces the cached `offline: true` snapshot; no connectivity/link event fakes online state.
- Safety: cached reads and offline/historical support restrictions remain unchanged. Support creation stays blocked while the effective Communications/session state is offline.
- Responsive UI: at widths below 360 logical pixels or text scale above 125%, the Messages title and support action stack vertically; a fixed spacing separates the header/action group from banners and conversation rows.
- Focused tests added for online banner absence, offline banner presence, state recovery, and 320x480 RTL/150% header separation while retaining teacher/support rows. Existing support restriction and row tests remain.
- Backend changed: NO. Migration: NONE. Commit/push: NOT RUN.
- `flutter analyze --no-pub`: PASS — no issues found (13.4s).
- `flutter test --no-pub`: PASS — 78 tests passed.
- `git diff --check`: PASS (line-ending conversion warnings only; no whitespace errors).
- Emulator diagnostics: Android reports the active Wi-Fi network as `INTERNET` + `VALIDATED`; airplane mode is off; TCP reachability to `10.0.2.2:8000` succeeds. ICMP ping is blocked/unanswered and was not treated as authoritative Internet evidence.
- Supervisor Android Emulator runtime acceptance: PASS. Backend/login/online Communications/recovery, existing School Support and teacher conversations, support entry/sheet, Arabic RTL fields, attachment and submit controls, floating labels, keyboard-safe submit action, and visual overflow checks all passed. Existing offline and historical restrictions remain unchanged.
- Closure commit: `e8884ea` (`Close student communications and school support`).

## Student Communications V1 Closure — implementation handoff

**Verification status: CLOSED / SUPERVISOR ACCEPTED**

- الفرع: `agent/codex-mobile`. تمت معاينة `design/student_v1/student_communications_v1.jpg` بصريًا واعتماد كثافة Nano، الرأس الداكن، البطاقات، فقاعات الرسائل، نموذج/حالة دعم المدرسة، وحالات loading/empty/error/offline.
- Notifications: قائمة/فلتر غير المقروء/badge/read/read-all، مع بقاء المقروء والتاريخي قابلين للفتح دون mutation تاريخية، وwhitelist للروابط المدعومة مع fallback آمن.
- Announcements: قائمة/تفاصيل/receipt read state/metadata المرفقات/inquiry gating وإنشاء محادثة الاستفسار، مع منع الاستفسار التاريخي والأوفلاين.
- Messages: قائمة/عداد غير المقروء/تفاصيل/توقيت/حالة تحميل وخطأ/كاش أوفلاين/تعطيل composer أوفلاين وتاريخيًا/إرسال نص ومرفقات دون queue أوفلاين.
- School Support: الفئات المدعومة، إنشاء الطلب، عرضه ضمن التاريخ، الحالة العربية، التفاصيل/ردود المدرسة، الرد، وإرفاق الملفات. عند نجاح الإنشاء وفشل المرفق تظهر partial-success message ولا يُلغى الطلب.
- Cache: استخدم `CachedContexts` الحالي بنطاق user + membership + academic year، مع resource منفصل لكل conversation؛ لا Drift schema change.
- Backend changes: NONE. Existing APIs were sufficient.
- Migrations: NONE.
- More/Profile وHome/Homework/Results/Attendance و`web_portal/`: لم تُنفذ فيها وظائف جديدة.
- `flutter analyze`: PASS — no issues.
- `flutter test`: PASS — 78 tests.
- Android Emulator runtime: SUPERVISOR PASS for online/offline recovery, support creation UI, RTL, keyboard handling, existing rows, and no visible RenderFlex overflow.

## Sprint 5B.2 — Student Homework

- Baseline `56cf542`; Flutter-only Student Homework implementation. Backend production files and migrations unchanged.
- Nano Homework visual reference received/readable/reviewed; production-quality RTL list/detail/status/action treatment PASS.
- Real API list/detail/submission draft/update/final-submit integrated through remote/local/repository/controller boundaries.
- Drift schema v3 additive scoped Homework cache + Local Draft; logout purge covers both while font preference remains.
- Local Draft survives tab, restart, and offline; submit is online-only and clears the draft only after server confirmation.
- Attachment metadata cached in Drift; online bytes download to app-private cross-platform documents storage. Viewer/LRU engine deferred.
- Format PASS; analyze PASS; 36/36 tests PASS; Debug APK PASS. Existing compileSdk maintenance warning remains non-blocking.
- Samsung SM N986U real `demo_student_a_02` flow PASS: login, list/detail, draft, restart, offline cache/banner/block, recovery, final submit, `submitted` state.
- iOS shared architecture/package review retained; native macOS/Xcode gate pending and non-blocking on Windows.
- No Backend tests rerun. No git add, commit, or push.
- Decision: **SPRINT 5B.2 STUDENT HOMEWORK ACCEPTED — READY FOR RESULTS & ATTENDANCE**.

## Sprint 5B.1 — Student Home + Timetable

- Flutter-only Student Home/Today/Week/Current/Next with Drift schema v2 real cache; Backend/migrations unchanged.
- Nano Student and shared Context visual references received and reviewed; production-quality visual QA PASS.
- Presentation-only closeout added the year to the context header, differentiated Current/Next emphasis, and made the cached-data banner subtle; API/repository/Drift/offline logic unchanged.
- Format/analyze PASS; tests 26/26 PASS (including long Arabic names, 150% scaling, and Tajawal/Cairo/Noto Sans Arabic); debug APK PASS after clearing a Windows lock on generated assets.
- Samsung SM N986U real login/API/Home/Today/Week/Current/Next PASS.
- Physical offline gate PASS: cached timetable + banner + last updated remained without reverse; fresh refresh restored after reverse.
- The Samsung device was not visible to ADB during this final visual-reference pass; the already accepted physical Home/Today/Week/offline evidence remains the device record.
- Backend production changes/migrations: NONE. Backend tests were not rerun. No git add, commit, or push.
- Decision: **SPRINT 5B.1 STUDENT HOME & TIMETABLE ACCEPTED — READY FOR HOMEWORK**.

## Sprint 5B.0 — Student Design System + Offline Foundation

- Baseline `8c7899d`; Flutter-only implementation and documentation. Backend/migrations unchanged.
- Cross-platform Android+iOS architecture retained: shared codebase, Drift app-private paths, secure storage, offline fonts, RTL, SafeArea, identical tenant isolation and logout purge.
- Flutter 3.24.5 / Dart 3.5.4. Pinned compatible stack: drift/drift_dev 2.22.1, drift_flutter 0.2.4, shared_preferences 2.5.3, build_runner 2.4.13.
- Drift schema v1, user/membership/year/resource scope, atomic cache writes, historical metadata, invalidation/purge, repository fallback, and lightweight real context cache implemented.
- Design tokens/components, Tajawal/Cairo/Noto Sans Arabic, persistent font setting, and five-tab Student placeholder shell implemented; no Student business feature started.
- `flutter pub get` PASS; format PASS; analyze PASS; tests 20/20 PASS; debug APK build PASS.
- Android physical device acceptance PASS on Samsung SM N986U (`R5CN81DGDXJ`): `flutter run` installed/launched successfully; `adb reverse tcp:8000 tcp:8000` enabled the `127.0.0.1` development API URL.
- Real Demo Student authentication and single School Noor context routing PASS. Foundation remained stable without Backend/network; Drift isolation/purge/font persistence tests remain PASS.
- Full Student dataset offline acceptance is mandatory in 5B.1 because Student Home/Timetable datasets do not exist in 5B.0.
- iOS package/architecture review PASS; native simulator/phone/archive gate remains pending macOS/Xcode and is not the rejection reason.
- Decision: **SPRINT 5B.0 DESIGN & OFFLINE FOUNDATION ACCEPTED — READY FOR STUDENT HOME & TIMETABLE**.

## Sprint 5A — Final Acceptance

- Documentation-only acceptance finalization; no production or backend code and no migrations changed.
- Previous rejection cause: environment-only Windows symlink/Developer Mode issue; now resolved.
- `flutter doctor`: PASS — no issues found.
- `flutter pub get`: PASS — got dependencies and exited successfully.
- `flutter analyze`: PASS — no issues found.
- `flutter test`: 7/7 PASS.
- Dependency versions were not updated; available package updates are not an acceptance failure.
- Real Demo API smoke was not rerun because code has not changed since the accepted smoke. Prior evidence remains PASS: `demo_teacher_multi` login, 2 contexts, `X-School-Membership-ID` scoped `auth/me`, and `RUNSERVER_COUNT=0`.
- Full backend tests were not run. Student, Parent, and Teacher Apps were not started.
- `BACKEND_UX_CONTRACT_V1.md` and `BACKEND_UX_CONTRACT_REPORT.md` remain outside this task.
- No git add, commit, or push was performed.

Decision: **SPRINT 5A FLUTTER FOUNDATION ACCEPTED — READY FOR STUDENT APP**.

## Sprint 4.7.1 — Timetable Integrity & Grid Hardening

- `ROADMAP.md` updated after acceptance with the complete Deferred/Future register (28 groups), actual Sprint 4.7/4.7.1 residual risks, and the fixed short path through Flutter Foundation; no deferred feature was implemented.
- Daily attendance is Classroom+Section/day (`not_recorded`/`partial`/`recorded`) with recorded/expected counts, not period attendance.
- `can_take_attendance` is limited to the owning Teacher in a writable current context on today's eligible lesson; Student/Parent/Admin/historical are false.
- Added used working-day and used-period mutation/deletion guards.
- Bulk/copy use one clear-first projected final state; clear+move, swap, validate-only and copy day/week parity pass atomically.
- Targeted 19/19 PASS; Full Core 609/609 PASS; Coverage 93% (10,925 statements / 770 missing); Teacher Today query budget 8.
- Django check PASS; no migration drift; Ruff PASS; OpenAPI 0 errors / 0 warnings. No migration added.
- Minimal HTTP smoke: Teacher Today 200, Student Today 200, Parent Week 200, used-day config 400, clear+move validation 200, copy-day clear-target preview 200; temporary server stopped. No git add, commit or push.

## Sprint 4.7 — Timetable & Daily Schedule

- Baseline `06c5e08`; existing untracked Backend UX Contract files preserved unchanged.
- Added Config/Period/Entry models and additive migration 0024.
- Added atomic conflict/bulk/validate/copy services and role-scoped Grid/Today/Week/Current/Next APIs.
- Demo Seeder now creates independent multi-school and historical timetable data.
- Targeted timetable tests: 15 current tests; Full Core final command 604/604 PASS plus final query-budget test PASS.
- Coverage 93% (10785/800); Ruff PASS; Django check PASS; migration drift none; OpenAPI 0/0.
- Live HTTP Teacher/Student/Parent/Admin succeeded; temporary server stopped, count zero.
- Decision: **SPRINT 4.7 TIMETABLE ACCEPTED — READY FOR BACKEND UX CONTRACT**.

## Sprint 4.6 — Demo Data + E2E Acceptance

- Baseline: clean `503f7b6`.
- Baseline `manage.py check`: PASS.
- Baseline migration drift: `No changes detected`.
- مرحلة التنفيذ الحالية: Management Command للـDemo مع guard وatomic/idempotent/reset محدود بالـprefix.
- فشل أول تشغيل للأمر: `User.password` فارغ أثناء `update_or_create` قبل `set_password`؛ لم تبق بيانات جزئية بسبب `transaction.atomic`. الإصلاح: إنشاء المستخدم الجديد بـpassword hash قبل أول save.
- فشل التشغيل الثاني: مولد `Teacher.employee_code` القديم لا يزيل الحرف `T` قبل التحويل الرقمي، فيكرر `T00001`. لم تبق بيانات جزئية. عزل الـSeeder أكواده إلى `DEMO_T*`، وسيضاف regression test وإصلاح إنتاجي محدود للسبب الجذري.
- اختبار reset كشف `ProtectedError` لأن Announcement يحمي creator membership. الإصلاح: حذف إعلانات مدارس Demo أولًا، ثم المدارس وبياناتها التابعة، ثم حسابات `demo_` المتبقية؛ لا يزال الحذف محصورًا بعلامة Demo.
- إعادة اختبار reset كشفت ترتيب `SET_NULL` مع قيد نتيجة منشورة: حذف Admin قبل نتيجة Exam المنشورة يخالف metadata constraint مؤقتًا. الإصلاح: حذف ExamResults التابعة لمدارس Demo قبل حذف المدرسة، مع بقاء النطاق محصورًا.
- E2E setup كشف عيب Active Context حقيقي: `Homework.clean` (وكذلك `Exam.clean`) كان يقارن `created_by.school` Legacy بمدرسة السجل، فيرفض المعلم متعدد المدارس في سياقه الثاني. الإصلاح المحدود: التحقق من Membership فعالة للمستخدم في مدرسة السجل ودور teacher/admin؛ لا تغيير للعقد.
- Full Sprint 4.6 targeted run كشف `PROTECT` مماثلًا في Conversation/Message أثناء reset بعد إضافة بيانات التواصل. أضيف حذف Conversations التابعة لمدارس Demo قبل حذف المدارس.
- أول Full Core بعد إصلاح Active Membership أظهر errors مبكرة في fixtures legacy بلا Membership، فأوقف التشغيل. الإصلاح المصحح يحافظ على fallback للـlegacy school فقط عندما لا توجد أي teacher/admin membership، ويستخدم العضوية الفعالة عند وجودها.
- اختبارات Exam/Homework legacy + multi-school targeted: 73/73 PASS.
- Full Core النهائي الأول: 590/590 PASS في 558.170s على PostgreSQL.
- Coverage full run: 590/590 PASS في 579.866s؛ TOTAL 93% (9950 statements / 710 missing).
- Django check PASS؛ deploy warnings الثلاثة المقبولة فقط؛ no model drift/pending migrations؛ Ruff PASS؛ OpenAPI 0/0.
- Live HTTP: login 200، contexts=2، missing header 409، وجميع موارد السياق المحدد الأساسية 200؛ RUNSERVER_COUNT=0.
- Database consistency: جميع فحوص duplicate/cross-school/publication/receipt/notification = 0.
- القرار: **SPRINT 4.6 E2E ACCEPTED — READY FOR FLUTTER**.

## المرحلة 1: Pre-flight وقراءة الوثائق

- الحالة: مكتملة.
- آخر Commit: `99a8f53 Sprint 4B.1: implement secure notifications, messaging, school inbox and communication hardening`.
- الشجرة غير نظيفة كما هو متوقع، وتحتوي تغييرات Sprint 4C/Stabilization غير الملتزمة.
- لم تظهر ملفات مجهولة خارج نطاق المشروع أو Sprint الحالي.
- `.coverage` ملف مولد ومحذوف حاليًا من working tree.
- الوثائق المقروءة: `AGENTS.md`, `PROJECT_CONTEXT.md`, `ROADMAP.md`, `README.md`, `SPRINT_4C.md`, `PROJECT_STABILIZATION_AUDIT.md`.
- الوثائق المطلوبة وغير الموجودة عند البداية: `SPRINT_4_5.md`, `ARCHITECTURE_FREEZE_V1.md`, `ARCHITECTURE_AUDIT_FINDINGS.md`, `ACTIVE_CONTEXT_MIGRATION_REPORT.md`, `SERVICE_BOUNDARIES.md`, `API_CONTRACT_V1.md`, `FLUTTER_BACKEND_CONTRACT_V1.md`, `PRODUCTION_READINESS_CHECKLIST.md`, `PROJECT_STABILIZATION_AUDIT_FINAL.md`.
- لم يُنفذ `git add` أو `commit` أو `push`.

## المرحلة الحالية

## المرحلة 2: اختبارات القبول الأساسية

- اختبار Bug السابق: `Ran 1 test` — `OK`.
- مجموعة Sprint 4C: `Ran 19 tests` — `OK`.
- Full core suite على PostgreSQL: `Ran 561 tests in 342.699s` — `OK`.
- System check المصاحب للاختبارات: `0 issues`.
- Ruff: `All checks passed!`.
- سجلات provider/storage ذات مستوى ERROR أثناء Full Suite ناتجة عن اختبارات failure-isolation المقصودة، ولم تُفشل أي اختبار.

## المرحلة الحالية

## المرحلة 3: Full Acceptance النهائي

- Full core + Coverage: 577/577 — OK، Coverage 93%.
- Django check: 0 issues.
- Deploy check: التحذيرات التطويرية الثلاثة المقبولة فقط.
- Migrations: لا model drift، لا migrations معلقة، وجميع core migrations حتى 0023 مطبقة.
- Ruff: ناجح.
- OpenAPI validation: صفر errors وصفر warnings.
- Server smoke في development mode: health/schema/docs/redoc = 200، protected API = 401، Admin guest = 302.
- تم إيقاف الخادم؛ `RUNSERVER_COUNT=0`.
- `git diff --check` المحدد والكامل: ناجحان، مع تحذيرات line-ending فقط.
- لا أسرار؛ أزيلت `.coverage` و`.ruff_cache` و`__pycache__` المولدة.
- فشل أمر scan مجمع مرة واحدة قبل التنفيذ بسبب PowerShell quoting؛ قُسم إلى أوامر آمنة ونجحت الفحوص الفعلية.
- لم يُنفذ `git add` أو `commit` أو `push`.

## القرار النهائي

**BACKEND FREEZE ACCEPTED — READY FOR SPRINT 5**

التقرير الكامل ذو الخمسين بندًا موجود في `BACKEND_FINAL_ACCEPTANCE_REPORT.md`. لم يبدأ Sprint 5 أو Flutter.

## Sprint 5A — Flutter Foundation

- Baseline backend `565f672`; no backend production logic or migration changed.
- Created `mobile_app/` with Riverpod, Dio, secure storage, GoRouter, typed auth/context models, repositories, and a session state machine.
- Added Arabic RTL login, context selector, historical read-only banner, unsupported-admin state, and Student/Parent/Teacher placeholder shells.
- Corrected the Active Context header to `X-School-Membership-ID` and default route to `auth/context/default/` after the first live smoke exposed the mismatch.
- Dart format PASS; Flutter analyze PASS; Flutter tests 7/7 PASS.
- Real Demo smoke PASS: login `demo_teacher_multi`, 2 contexts, membership-scoped `auth/me`; temporary server stopped and final `RUNSERVER_COUNT=0`.
- The former `flutter pub get` failure was environment-only (Windows symlink/Developer Mode); the issue is resolved and the command now passes.
- No full backend tests or coverage rerun. No git add, commit, or push.

Decision superseded by the final accepted decision at the top of this report.
