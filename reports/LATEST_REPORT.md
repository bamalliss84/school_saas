# Latest Acceptance Report

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
