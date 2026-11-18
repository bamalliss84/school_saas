# Latest Report

## 2026-11-18 — UX and accessibility review

**Method:** an automated audit of all 19 web pages in the browser (as school admin), plus a code scan of the web and app source.

**Web — findings and fixes:**
- **Search boxes and filter dropdowns without a label** on about 10 pages. A screen reader announced them as just "edit field".
  - The shared `Input` component now uses the placeholder as the accessible name when there is no visible label. It also links the error or hint message to the field (`aria-describedby`), marks the field `aria-invalid`, and the error message uses `role="alert"`.
  - Clear names were added to 19 standalone fields in `OperationsPage` (timetable, attendance, homework, announcements, messages, data), `StudentsPage`, `ResponsiveFilterBar` and `ContextSelectorModal`.
- **Pages without a main heading (h1):** fees, subscription, change password, and the platform page. They now use h1, with the same look (18px).
- Rerunning the audit: every page has one h1, and there are 0 unnamed fields and 0 unnamed buttons. The page language and direction (`lang=ar`, `dir=rtl`) are correct.
- Test added: `InputA11y.test.tsx` (5 tests).

**App — findings and fixes:**
- 13 icon buttons (back, send, attach file, sign out) had no description. They now have Arabic `tooltip`s, which screen readers also read.
- **The back arrow pointed the wrong way** on 6 screens: `Icons.arrow_forward` mirrors in Arabic and points left. I confirmed in the Flutter source that both icons mirror (`matchTextDirection: true`), so I standardized on `arrow_back`, the same as `BackButton`.
- Updated one test to find the back button by its tooltip instead of its icon.

**Development environment (not a code bug):** after a restart, Windows reserved ports 8000 and 5173 (ranges 7974–8073 and 5141–5240). I didn't change any system settings. The Vite dev port and proxy target can now be set through `VITE_DEV_PORT` and `VITE_API_PROXY_TARGET`, and the defaults are unchanged.

**Verification:**
- Web: typecheck ✓, lint ✓, **178 tests ✓**, build ✓.
- Flutter: **238 tests ✓**; analyze shows 19 notes, all pre-existing.
- Backend: check ✓, makemigrations --check ✓; no backend code changed.
- Servers were stopped after the audit.

## 2026-11-16 (update 2) — Preparing the app for the stores

**Real bug fixed:** the main Android manifest didn't declare the internet permission (Flutter adds it in debug builds only). A store build could not have connected to the server at all.

**What was done (all in `mobile_app`):**
- `android/app/build.gradle`: release signing comes from `android/key.properties` (already ignored by git, as are `*.jks`). Without that file the build uses the debug key and prints a clear warning. The default Flutter TODO comments were removed.
- `AndroidManifest.xml`:
  - internet permission;
  - name taken from `strings.xml`: "بوابة المدرسة" (temporary);
  - `allowBackup=false`;
  - unencrypted traffic blocked.
- Debug build only: plain HTTP allowed to `10.0.2.2`, `localhost` and `127.0.0.1` (`network_security_config_debug.xml`).
- `AppEnvironment.releaseProblem` and `bootstrap.dart`: a store build with a server address that isn't HTTPS, or that points to a local server, won't start and shows a clear Arabic message instead of sending data.
- iOS: display name "بوابة المدرسة". Version `1.1.0+2`.
- New guide: `docs/STORE_RELEASE.md`. It covers creating the signing key, building, Play requirements (privacy, Data safety, review account), and what is waiting on the owner.

**Tests:** `test/app_environment_test.dart` (3 tests).

**Verification:**
- Flutter: **238 tests ✓**; analyze shows 19 notes, all pre-existing.
- A real release APK build ✓ (28.5MB). Inspected with `aapt`: package `com.schoolsaas.school_saas_mobile`, versionCode 2, internet permission present, Arabic name, `allowBackup=0`, `usesCleartextTraffic=0`.
- Backend: check ✓, makemigrations --check ✓. No backend code changed after the last full run (848 OK).

**Waiting on the owner:** the final app ID (it can't be changed after the first upload), the product name, the logo (for the icon and splash screen), the server address, and Google Play and Apple accounts.

## 2026-11-16 — Error monitoring (email alerts)

**Decision:** `sentry-sdk` isn't installed, and adding it is a new external dependency I can't test here. I used email alerts through the SMTP that already exists instead. They turn on only when `ERROR_ALERT_EMAILS` is set, and Sentry can be added later.

**What was done:**
- `core/monitoring.py`: a logging handler that sends a short email for every server error.
  - Contents: error type, method and path (without the query string), and the code location (file, line, function).
  - It never includes the error message, the request body, headers, cookies, variables or any user data.
  - The same error is sent at most once every `ERROR_ALERT_THROTTLE_SECONDS` (default 10 minutes).
  - A mail failure never breaks the request.
- Linked to `django.request` and `core` in `settings.py`. The duplicate record Django logs for every 5xx response is ignored.
- `api_exceptions.py`: unhandled API errors are now logged with the request, so the alert shows the path.
- `run_billing_jobs`: a failure is logged (so an alert is sent), and the job still exits with a failure code.
- `.env.production.example` and `docs/DEPLOYMENT.md` updated.

**Tests:** `core/test_r11_monitoring.py` has 9 tests:
- off by default;
- an alert with no personal data (name, ID number, token, query and body are all checked);
- throttling, and disabling it;
- no alert for warnings or 404;
- a mail server failure doesn't break anything;
- an API 500 sends exactly one alert with the path;
- a billing job failure is alerted and the job still fails.

**Verification:** check ✓, makemigrations --check ✓ (no migration), ruff ✓, and the settings load in production mode. Full backend: **848 tests OK**.

## 2026-11-15 (update 4) — Automatic daily jobs and backups

**What was added to `docker-compose.prod.yml` (no crontab needed on the server):**
- Service `jobs`: runs `run_billing_jobs` (fee reminders and past-due subscriptions) every day at `BILLING_JOB_HOUR_UTC` (default 4 UTC), and once on startup. The job is idempotent and doesn't repeat notifications.
- Service `backup`: every night at `BACKUP_HOUR_UTC` (default 23 UTC) it backs up the database (`pg_dump -Fc`) plus an archive of the `media` files into `backups/`, and deletes files older than `BACKUP_KEEP_DAYS`. Files are written under a temporary name first, so a failed run never leaves a file that looks like a valid backup.
- A shared scheduler script, `deploy/scheduler/daily.sh`: it logs a failure and retries the next day, and rejects an invalid hour.

**Files:**
- New: `deploy/scheduler/daily.sh`, `deploy/scheduler/backup.sh`.
- Edited: `docker-compose.prod.yml`, `.env.production.example` (three new settings, no secrets), `docs/DEPLOYMENT.md` (section 4 and the pre-launch checklist), `scripts/backup_db.sh` (comment only: it is now for manual backups), `docs/ROADMAP_TO_LAUNCH.md`.

**Actual testing with Docker:**
- `docker compose config` is valid with a temporary environment file, deleted afterwards.
- Real PostgreSQL 16:
  - the backup produced a dump file that contains the table's data, plus a media archive with the files;
  - when the database wasn't ready yet, the run failed cleanly and left no fake backup;
  - the scheduler ran the job on start and computed the next run correctly;
  - an invalid hour is rejected.
- Test containers and files were deleted afterwards.
- Not tested: building the `backend` image itself (it needs `python:3.13-slim` downloaded). The `jobs` service uses the same image and command as before.

**Verification:** check ✓, makemigrations --check ✓ (no migration). Full backend: **839 tests OK**.

## 2026-11-15 (update 3) — Full demo data + manual web QA

**Demo data (`seed_demo_school`):**
- New user `demo_teacher_parent`: a teacher and a parent in the same school (demo Al-Noor school). It is separate so the existing demo accounts keep a single role and the existing tests don't change.
- School fees: two installments for three students, partly paid and overdue payments, and two receipts.
- A demo plan; School A has an active subscription; School B is past due with an open invoice.
- Repeating the command creates no duplicates; `--reset-demo` deletes the billing rows before the schools.
- Test added: `test_release11_demo_has_teacher_parent_fees_and_subscriptions`.

**Manual web QA in the browser:**
- As school admin: all 19 pages open with data and no errors, including the fees tabs and the subscription page. The fee totals match the data (overdue 95,000).
- As platform owner: summary, plans and invoices are correct.
- Fixed:
  - **The home page requested a nonexistent endpoint `dashboard/admin/`**, which produced a 404 on every visit. The call was removed; the data was already built from the other APIs.
  - **The platform owner (no school selected) landed on an empty school dashboard.** They are now sent to `/platform` automatically. Test added.

**Failures during the work and how they were fixed:** the first version of the seed made `demo_teacher_a` a parent as well. That broke 2 tests in `test_sprint46_e2e_acceptance` (`MultipleObjectsReturned`), because they expect a single role per school. Fix: the separate user above, with no change to the tests.

**Verification:** check ✓, makemigrations --check ✓ (no migration), ruff ✓, web lint ✓, 173 tests ✓, build ✓. Seed and e2e tests: 18 OK. Full backend: **839 tests OK**. Servers were stopped after QA.

## 2026-11-15 (update 2) — Review of complex cases + parent app completion

**Backend review (no changes needed, covered by tests):**
- A user can be a teacher and a parent at the same time: a separate membership per (user, school, role). Covered by `test_sprint4d_multischool_roles`.
- A teacher can teach in more than one school: assignments and students are isolated by active context. Same test file.
- Student transfer:
  - the old enrollment is kept and its membership becomes historical (read-only);
  - parent memberships are updated;
  - nothing is copied.
  - Covered by `test_sprint4d_student_transfer` and `test_sprint4d1_consistency`.
- A parent can start a private conversation with their child's teacher. Covered by `test_sprint4b1_communication_hardening`.

**Gaps fixed in the parent app:**
- **Role and school switching:** "More" used to show parent contexts only, so a teacher who is also a parent could not switch to their teacher role. It now shows every role and school, with Arabic role labels. The general context picker also shows Arabic labels instead of `teacher`/`parent`.
- **Messaging the child's teacher:** a new "مراسلة معلم" button. The list comes from safe discovery (only the selected child's current teachers), then a private `teacher_parent` conversation is created. It is hidden in historical and offline contexts.
- **Academic record:** a new "السجل الدراسي" screen from the home page. It lists the schools the child attended with their years, and opens a previous school's record read-only through its historical context.
- **Bug fix:** the subject dialog in conversations disposed its text controller before the dialog closed, which could crash. It is now a separate widget that owns its controller.

**Verification:** Flutter 232 tests ✓, analyze 19 notes (all pre-existing). Backend: check ✓, migrations ✓, ruff ✓, **838 tests OK**. Teachers can now also start a private conversation with a student's guardian (safe discovery + signed reference); Flutter 235 tests ✓.

## 2026-11-15 (update) — Consistency and completion

- **Attendance:** the Super Admin who selects a school now sees only that school's attendance and assignments (the 1.1 decision). Removed `request.user.role/school/academic_year` from `attendance/daily/`; it uses the active context now. Updated the test that documented the old behavior to the new decision, and extended it to cover the daily report.
- **Change password:**
  - Web: a page at `/account/password` plus a link in the user menu.
  - Mobile: a "تغيير كلمة المرور" item in the "More" list for parent, student and teacher. After a successful change, the user is signed out of all devices.
- **Web performance:** pages load per route (lazy). The main bundle went from 567KB to 306KB.
- **Plan:** `docs/ROADMAP_TO_LAUNCH.md`.
- **Verification:** web 172 tests, lint, typecheck and build ✓. Flutter 226 tests ✓, analyze shows no new issues. Backend: **838 tests OK** after adding a legacy-compat fallback in `attendance/daily/` (tests that use force_authenticate have no active context).
- **Migrations:** none.

## 2026-11-15 — Release 1.0.1 (production readiness) + Release 1.1 (fees and subscriptions)

**Branch:** `release/1.1-dev` (from `main` at `db996f2`; merged `agent/codex-mobile`, no new changes). Not merged into `main`.

### 1.0.1 — Production readiness
- **Production settings guard:** with `DJANGO_ENV=production`, the server refuses to start if the secret key, DEBUG, ALLOWED_HOSTS, the database password or email settings are unsafe. Also enabled: HTTPS redirect, proxy header and Referrer-Policy.
- **Password reset by email:**
  - Request, confirm and change-password endpoints, with throttling.
  - The request always returns the same message, so it never reveals whether an account exists.
  - A successful change revokes all of the user's sessions (tokens).
- **Web:** "Forgot password" and "Set new password" pages, plus starter Terms and Privacy pages (these need legal review).
- **Mobile:** "Forgot password?" screen on the login page.
- **Deployment:**
  - Dockerfiles for the server and the web, `docker-compose.prod.yml`, nginx, `.env.production.example` (no secrets).
  - Backup and restore scripts.
  - An Arabic deployment guide in `docs/DEPLOYMENT.md`.
- **Pre-existing bug fixed:** generating the parent code made adding a second parent in any school fail (IntegrityError). Fixed, with a regression test.

### 1.1 — School fees for parents
- **Models (migration `0027_billing_and_fees`):** `FeeCategory`, `StudentFee` (with installments and discount), `FeePayment` (receipt number unique per school, void instead of delete).
- **Admin API, isolated by school:**
  - fee categories;
  - issuing fees: preview first, then confirm; targets the whole school, a class, a section or chosen students; installments must add up to the total;
  - recording a manual payment: locks the row, cannot exceed the balance or be dated in the future;
  - voiding a payment, cancelling a fee that has no payments;
  - a collection summary and filters.
- **Parents:** only guardians with `can_receive_financial_alerts` see fees or get alerts; other guardians get 404.
- **Notifications (after commit, deduplicated):** fees issued, payment received, a reminder 3 days before the due date, and a weekly overdue reminder.
- **Daily job:** `manage.py run_billing_jobs`.
- **Web (school admin):** `/fees` page with an overview, student fees, issue fees with preview, payments and receipts with printing, and fee categories. Write actions are hidden in historical read-only contexts.
- **Parent app:** an alert card on the home screen for the selected child (overdue or next installment), and a fees page with summary, installments and receipts. It works offline from a cache isolated per child and membership, and is read-only.

### 1.1 — Platform subscriptions for schools
- **Models:** `SubscriptionPlan`, `SchoolSubscription` (only one current subscription per school, history kept), `PlatformInvoice`, `PlatformPayment`.
- **Platform owner** (super_admin with no school selected):
  - `/platform` page with summary, schools and subscriptions, plans and invoices;
  - invoice amount = base price + price per student × active students;
  - full payment reactivates a past_due subscription.
- **School admin:**
  - `/subscription` page, read-only;
  - a warning banner at the top of the admin app (past due, suspended, expired, expiring soon, over the student limit).
- **Daily job:** marks subscriptions with overdue invoices as `past_due`.

### Verification
- Backend: check ✓, makemigrations --check ✓ (after 0027), ruff ✓, **838 tests OK**.
- Web: typecheck ✓, lint ✓, **169 tests** ✓ (22 files), build ✓ (only a bundle-size warning).
- Flutter: analyze shows 20 notes, all pre-existing and none in the new files; **224 tests** ✓.
- No servers left running.

### Open points
- The gateway is not connected (payments are recorded manually, as decided).
- The legal texts need review.
- Production email settings must be filled in before going live.
- Teacher-to-parent conversations are postponed to a later release.

---

## 2026-11-13 — Release 1.0 Admin: READY

- **الاعتماد:** اعتمد مالك المشروع الإصدار بعد مراجعة `docs/RELEASE1_FINAL_REVIEW.md`.
- **آخر تحقق:** 797 اختبار خادم OK، و154 اختبار ويب، وcheck وmigrations وruff وlint والبناء ناجحة، وتحقق Excel الحي ناجح.
- **لم يُنفذ:** لا commit ولا push ولا دمج في `main`.
- **التالي:** متطلبات التشغيل الفعلي (القسم 5 في مستند المراجعة)، ثم الإصدار 1.0.1.

## تحديث 2026-11-13 — تجهيز المراجعة النهائية

- **المستند:** `docs/RELEASE1_FINAL_REVIEW.md`: أدلة كل مرحلة، والقرارات، ونتائج التحقق، ونقاط غير حاجبة، ومتطلبات التشغيل الفعلي، وقسم توقيع.
- **مراجعة الفرق:** كل التغييرات ضمن النطاق. لا Mobile ولا أسرار ولا ملفات محظورة متتبعة.
- **الويب:** typecheck وlint ناجحان، و154 اختبارًا ناجحة، والبناء ناجح.
- **تحقق Excel الحي:** الرفع ثم المعاينة، والقالب، وتصدير الطلاب والحضور كلها 200. أُلغي التأكيد فلم تُكتب بيانات. أُوقف الخادمان.
- **ملاحظة تشغيل:** إيقاف مهمة Vite الخلفية لم ينهِ عملية node؛ أُنهيت يدويًا وتأكدت أن المنفذين مغلقان.
- **الخادم:** check ناجح، No changes detected، ruff ناجح، **797 اختبارًا OK**.
- **Migrations:** لا يوجد. لا commit ولا push.
- **ليس READY** حتى توقيعك.

## تحديث 2026-11-13 — قرار Super Admin في الحضور

- **القرار:** نقل رؤية حضور كل المدارس إلى لوحة مالك المنصة في إصدار 1.1. لا تغيير في كود 1.0؛ السلوك الحالي يبقى موثقًا باختبار.
- **مهمة 1.1:** إنشاء لوحة المالك، وحصر Super Admin داخل الـ API المدرسية في Active Context، وإزالة قراءة `request.user` القديمة من `attendance/daily/`.
- **الملفات:** `tasks/CURRENT_TASK.md`، `docs/RELEASE1_ADMIN_F1F_F1N.md`، وهذا التقرير. توثيق فقط، فلا اختبارات جديدة ولا migration.
- **بوابة READY:** المتبقي الحاجب الوحيد هو مراجعتك النهائية الموثقة. **ليس READY بعد.**

---

## الجولة الرابعة — F1L-6 Excel ومراجعة المنتج وخطة الإصدارات

- **القرار:** اعتمدتَ Excel بدل CSV، وإضافة مكتبة `openpyxl==3.1.5` (أضيفت إلى `requirements.txt`).
- **Migrations:** لا يوجد. **Mobile:** لم يُعدَّل. لا commit ولا push.
- **مستند الخطة:** "خطة منصة المدارس — المراجعة وخارطة الإصدارات" (مستند Claude Docs): ما فهمته من الكود، نقاط القوة، الفجوات قبل البيع، المقارنة بالأنظمة العالمية، التصميم وتجربة المستخدم، خارطة الإصدارات 1.0 ← 1.0.1 ← 1.1 ← 2.0، الباقات وخطة البيع، المخاطر، القرارات المطلوبة.

### ما نُفذ في Excel

| الجزء | التفاصيل |
|---|---|
| قالب الاستيراد | `GET /api/v1/admin/data/template/?kind=students|teachers|guardians`: عناوين عربية، ورقة RTL، أعمدة الأكواد والجوال والهوية بتنسيق نص، وورقة "تعليمات". كلمات المرور ليست في القالب. |
| رفع ملف Excel | `POST /api/v1/admin/data/import/parse/` (multipart): يحوّل الملف إلى صفوف ثم يمر بنفس مسار المعاينة ثم التأكيد الموجود (`admin/data/import/`)، فلا يوجد مسار كتابة جديد. يقبل العناوين العربية أو أسماء الحقول، ويحوّل القيم العربية (ذكر/أنثى، أب/أم...، نعم/لا). CSV يبقى مدعومًا. |
| التصدير | `admin/data/export/?output=xlsx` للطلاب والمعلمين وأولياء الأمور، وأنواع جديدة: الحضور والنتائج والجدول والواجبات، مع فلاتر التاريخ والصف والشعبة. عقد JSON الحالي لم يتغير. |
| الحماية | حد 5MB للملف و50MB بعد فك الضغط (ضد الملفات المضغوطة الخبيثة)، و1000 صف و50 عمودًا، وقراءة `read_only` دون تنفيذ معادلات، ومنع حقن المعادلات في التصدير (`=`, `+`, `-`, `@`)، وحد 20,000 صف للتصدير مع طلب تضييق النطاق. |
| الصلاحيات | المدير فقط. السياق التاريخي يصدّر سنته ويُمنع من الاستيراد (403). المعلم 403. كل الاستعلامات مقيدة بالمدرسة والسنة النشطة. |
| الويب | اختيار النوع (7 أنواع)، "تنزيل قالب Excel"، رفع Excel أو CSV، "تصدير Excel" مع فلتر التاريخ للأنواع التشغيلية، وإخفاء الاستيراد للأنواع التشغيلية وفي السياق التاريخي. |

### الملفات

- جديدة: `backend/core/services/spreadsheets.py`، `backend/core/services/data_exchange.py`، `backend/core/test_r1_f1l_excel.py` (16 اختبارًا)، `web_portal/src/utils/excel.ts`.
- معدلة: `backend/core/admin_release_views.py` (التصدير ونقطتا القالب والتحويل)، `backend/config/api_urls.py`، `requirements.txt`، `web_portal/src/services/apiClient.ts` (`responseType: 'blob'`)، `web_portal/src/pages/OperationsPage.tsx` (واجهة البيانات فقط)، `web_portal/src/__tests__/ReleaseOneAcceptance.test.tsx` (+5 اختبارات F1L)، `docs/RELEASE1_ADMIN_F1F_F1N.md` (قرار F1L-6)، `tasks/CURRENT_TASK.md`.

### التحقق

| البوابة | النتيجة |
|---|---|
| `manage.py check` | ناجح |
| `makemigrations --check --dry-run` | No changes detected |
| `ruff check` | ناجح |
| `manage.py test core` | **797 اختبارًا OK** |
| Web typecheck / lint | ناجح / ناجح (خطأ نوع واحد في اختبار جديد أُصلح وأُعيد الفحص) |
| Web test | 20 ملفًا و154 اختبارًا ناجحة |
| Web build | ناجح (إلى مجلد مؤقت) |
| السيرفر | لم يُشغَّل في هذه الجولة؛ التحقق عبر APIClient واختبارات الويب |

### المتبقي

- **ليس READY:** قرار المدير العام في الحضور، ثم مراجعتك النهائية.
- استيراد الطلاب ينشئ الطالب دون تسجيله في صف (سلوك سابق). أقترح إضافة عمودي الصف والشعبة إلى القالب في 1.0.1.
- رسائل أخطاء التحويل من الخادم بالإنجليزية (مثل اسم العمود غير المعروف)، كبقية رسائل الـ API.
- لم يُجرَّب رفع ملف Excel حقيقي من المتصفح على السيرفر الحي في هذه الجولة.

---

## Release 1.0 Admin F1F–F1N — الجولة الثالثة: إغلاق الفجوات والمراجعة

- **الفرع:** `feature/release1-admin-f1f-f1n` (القاعدة `2474dae`). لا commit ولا push ولا merge.
- **المرجع:** `docs/RELEASE1_ADMIN_F1F_F1N.md`، والحالة التفصيلية في `tasks/CURRENT_TASK.md`.
- **Mobile:** لم يُعدَّل. **Migrations:** لم تُنشأ (لا تغيير في models).
- **النتيجة:** **ليس READY.** كل المراحل مكتملة بأدلة عدا F1L (متوقفة على قرار F1L-6)، وهناك قرار معماري معلق بشأن Super Admin في الحضور.

### 1. حالة المراحل

| المرحلة | الحالة | الدليل المختصر |
|---|---|---|
| F1F الجدول | مكتملة | إعداد الأيام والفترات، والشبكة، وإضافة/استبدال/مسح بتحقق مسبق، والتعارضات دون حفظ جزئي، ونسخ يوم/أسبوع بمعاينة، والقراءة فقط. Web ×7 + `test_sprint47_timetable_*` + تحقق حي |
| F1G الحضور | مكتملة | ملخص يومي، وتسجيل جماعي لغير المسجلين، وتصحيح، وعزل، وسياق تاريخي. `test_r1_f1g_attendance.py` (9) + Web ×2 |
| F1H الواجبات | مكتملة | إنشاء عبر صف ← شعبة ← مادة ← تكليف، والنشر والإغلاق والتسليمات والقراءة فقط. Web ×3 + اختبارات Sprint 4A/M2.5 |
| F1I التواصل | مكتملة | جمهور الإعلانات بحمولة الويب الفعلية، وسير عمل الدعم، والرد والإغلاق. `test_r1_f1i_communications.py` (8) + Web |
| F1J الاكتشاف الآمن | مكتملة | محمي في الخادم وليس بإخفاء الواجهة فقط. `test_r1_f1j_safe_discovery.py` (16) |
| F1K التهيئة | مكتملة | `F1KOnboardingTests` (4) + Web |
| F1L الاستيراد والتصدير | **متوقفة** | F1L-1..5 مغلقة (`F1LImportExportTests` 5 + Web). F1L-6 ينتظر قرارًا |
| F1M التقارير | مكتملة | `F1MReportsTests` (3) + تصدير CSV في الويب |
| F1N الإعدادات | مكتملة | `F1NSettingsTests` (4) + `F1NLogoTests` (3) + Web |

### 2. خلل وظيفي وأمني اكتُشف وأُصلح (الجولات 2–3)

| المرحلة | الخلل | الإصلاح |
|---|---|---|
| F1I | جمهور غير صالح للإعلان (أدوار فارغة، صف أو شعبة من مدرسة أخرى) يرجع **500** لأن `ValidationError` من `full_clean` في النموذج لا يتحول إلى خطأ DRF | `services/announcements.py::_validate_target` يحوّلها إلى DRF `ValidationError` فيرجع 400 برسالة السبب، ويغطي الإنشاء والتعديل. اختبار انحدار في `test_r1_f1i_communications.py` |
| F1I | جمهور "أدوار محددة" يرسل `target_roles: []` دائمًا، وجمهور الصف والشعبة غير متاح | اختيار الأدوار وصف وشعبة مستهدفين في الويب |
| F1I | لا سير عمل للدعم في الويب | إسناد ← متابعة ← حل بملاحظة، مع إخفائها في السياق التاريخي |
| F1G | مطابقة الشعبة في التسجيل الجماعي تفشل لأن `current_enrollment.section` كائن وليس رقمًا (اكتُشف بالتكامل الحي) | مقارنة `section.id`، وتصحيح بيانات الاختبار لتطابق الشكل الحقيقي |
| F1M | مدخلات تقرير خاطئة ترجع 500 | `_int_param` و`_date_param`، ورفض `date_from > date_to` |
| F1M | تصدير التقرير يكتب `\n` و`﻿` حرفيًا | `toCsv` و`downloadCsv` الموحدان |
| F1N | لا يوجد رفع شعار | `POST/DELETE /admin/settings/logo/` بتنسيقات PNG/JPEG/WEBP وحد 2MB، مع تحقق فعلي من الصورة وحذف الملف القديم بعد commit |
| F1K | خطوة "المعلمون" تكرر فحص التكليفات | فحص وجود معلم نشط |
| Web | الصفحة تُعاد تهيئتها مع كل إعادة تحميل، فتضيع حالة النماذج | `loadedModule` |
| Web | الحذف بلا تأكيد، والنماذج تُغلق حتى عند الفشل | `window.confirm`، والإغلاق عند النجاح فقط |

### 3. نقاط المراجعة المطلوبة

- **F1J محمي في الخادم:** فحص الدور (معلم أو ولي أمر فقط، والمدير والطالب 403)، ونطاق التسجيل النشط والتكليف أو الوصاية، و`recipient_ref` موقّع بـ salt خاص ومدة ساعة ومطابق للمدرسة والطالب والتكليف. التلاعب أو التزوير أو انتهاء الصلاحية أو مدرسة أخرى يرجع 400، والسياق التاريخي يرجع 403 عند البدء.
- **F1G الصلاحيات:** المدير يرى مدرسته فقط، والسجل الأجنبي يرجع 404 في القراءة والتعديل. التكليف أو التسجيل الأجنبي في الإدخال الجماعي يُرفض ذرّيًا. السياق التاريخي يقرأ ويُمنع من الكتابة بـ 403، وولي الأمر والطالب 403.
- **Super Admin في الحضور:** `get_attendance_queryset_for_user` يعيد سجلات كل المدارس، و`attendance/daily/` يقرأ `request.user` القديم. هذا متوافق مع قاعدة "super_admin يرى جميع المدارس"، لكنه يخالف مبدأ Active Context، وموثق باختبار. **يحتاج قرارك قبل أي تغيير.**
- **التكامل الحي (UI↔API):** شُغّل السيرفر وVite مؤقتًا بحساب demo المدرسة A وتم التحقق من:
  - الشبكة والخيارات والإعداد والفترات؛
  - الملخص اليومي والقائمة؛
  - أعلام الواجبات، ومحادثة الدعم، والإعلانات، و`logo_url`؛
  - رفض المدخل الخاطئ بـ 400، ومنع اكتشاف المدير بـ 403؛
  - `exact_duplicate`، ومعاينة النسخ دون تعديل.

  أُوقفت العمليتان بعد التحقق.

### 4. الملفات

- Backend:
  - `core/admin_release_views.py`: الاكتشاف، والتهيئة، والتقارير، والشعار.
  - `config/api_urls.py`: مسار الشعار.
  - `core/services/announcements.py`: 400 بدل 500.
- اختبارات Backend جديدة: `test_r1_f1g_attendance.py` و`test_r1_f1i_communications.py` و`test_r1_f1j_safe_discovery.py` و`test_r1_f1k_f1n_admin_release.py`.
- Web:
  - `pages/OperationsPage.tsx`: دون إعادة هيكلة.
  - `components/timetable/TimetableAdminTools.tsx`.
  - `utils/csv.ts` و`utils/timetable.ts`.
  - إصلاحات hooks في صفحات الطلاب والمعلمين وأولياء الأمور و`ClassSubjectModal`.
- اختبارات Web جديدة: `ReleaseOneAcceptance.test.tsx` (18) و`OperationsPage.test.tsx` (14) و`csv.test.ts` (4).
- CI: إضافة `npm run lint` إلى `.github/workflows/web-ci.yml`.
- التوثيق: `docs/RELEASE1_ADMIN_F1F_F1N.md` و`tasks/CURRENT_TASK.md` وهذا التقرير.

### 5. التحقق

| البوابة | النتيجة |
|---|---|
| `manage.py check` | ناجح، لا مشاكل |
| `makemigrations --check --dry-run` | ناجح، No changes detected |
| `ruff check backend/core backend/config` | ناجح |
| `manage.py test core` (قبل إصلاح الإعلانات) | 773 اختبارًا OK. ملف F1I أُنشئ بعد بدء هذا التشغيل فلم يُشمل |
| `test_r1_f1i_communications` (أول تشغيل) | **فشل 2**: 500 != 400. السبب والإصلاح في القسم 2 |
| F1I + F1G + `test_sprint4c_announcements` بعد الإصلاح | 52 اختبارًا OK |
| `manage.py test core` بعد الإصلاح | **781 اختبارًا OK** (يشمل F1I) |
| Web typecheck / lint (`--max-warnings 0`) | ناجح / ناجح |
| Web test | 20 ملفًا و149 اختبارًا ناجحة |
| Web build | ناجح (إلى مجلد مؤقت لأن `web_portal/dist/assets` مقفول على ويندوز) |

### 6. المتبقي

**حاجب لـ READY:**

1. **قرار F1L-6:** اعتماد CSV بدل XLSX/ImportJob لـ Release 1.0، وهل تصدير الحضور والنتائج والجدول والواجبات (GAP-EXCEL-02) ضمن النطاق. غير منفذ حاليًا.
2. **قرار Super Admin** في الحضور (القسم 3).
3. مراجعتك النهائية الموثقة.

**غير حاجب (مسجل):**

- تعديل وقت فترة موجودة و`periods/bulk` غير معروضين في الواجهة.
- نسخ الأسبوع غير مختبر في الويب منفصلًا (Backend مختبر).
- مرفقات الإعلانات ومعاينة الجمهور غير معروضة في ويب الإدارة.
- خدمة ملفات media للشعار في الإنتاج تحتاج إعدادًا.
- `OperationsPage.tsx` ما زال كثيفًا بأنواع `any`، وإعادة هيكلته مؤجلة حسب التعليمات.
