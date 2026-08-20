# School SaaS Roadmap

- **المشروع:** School SaaS
- **تاريخ آخر تحديث:** 2026-08-14
- **المرحلة الحالية:** المرحلة 12 — Flutter
- **Current sprint:** Sprint 5B.0 — Student Design System + Offline Local Data Foundation
- **نسبة التقدم التقريبية:** 78%
- **آخر Commit مرجعي معروف:** `06c5e08 Sprint 4.6: add demo data and end-to-end backend acceptance`

## حالات التنفيذ

- ⬜ لم تبدأ
- 🟡 قيد التنفيذ
- ✅ مكتملة
- ⛔ متوقفة
- 🔵 مخطط لها لاحقًا

# المرحلة 0 — تثبيت الأساس الحالي

**الحالة: ✅ مكتملة**



## الموجود

- [x] المدارس.
- [x] المستخدمون والأدوار.
- [x] السنوات الدراسية والفصول الدراسية.
- [x] الصفوف والشعب والمواد.
- [x] الطلاب وتاريخ تسجيلهم عبر `StudentEnrollment`.
- [x] أولياء الأمور وروابط `StudentGuardian`.
- [x] المعلمون وتكليفات `TeacherAssignment`.
- [x] الحضور الأساسي.
- [x] الاختبارات والنتائج.
- [x] `ExamResultLog`.
- [x] JWT Login.
- [x] عزل أولي بين المدارس.

## المتبقي

- [x] مراجعة شاملة للصلاحيات.
- [x] توحيد أخطاء API.
- [x] اختبارات Multi-Tenant.
- [x] Current User API.

# المرحلة 1 — المصادقة والصلاحيات

**الحالة: ✅ مكتملة**

- [x] `POST /api/auth/login/`
- [x] `POST /api/auth/refresh/`
- [x] `POST /api/auth/logout/`
- [x] `GET /api/auth/me/`
- [x] صلاحيات `super_admin`.
- [x] صلاحيات `school_admin`.
- [x] صلاحيات `teacher`.
- [x] صلاحيات `parent`.
- [x] صلاحيات `student`.
- [x] عزل المدارس.
- [x] منع الوصول المباشر إلى سجلات خارج النطاق.
- [x] إعادة التحقق من حالة المستخدم والمدرسة عند refresh وكل API محمية.
- [x] حماية Logout من إلغاء refresh token لمستخدم آخر.
- [x] تطبيق خصوصية guardians حسب الدور.

# المرحلة 2 — APIs البيانات الأساسية

**الحالة: ⬜ لم تبدأ**

- [ ] School profile.
- [ ] School settings.
- [ ] Academic years.
- [ ] Academic terms.
- [ ] Classrooms.
- [ ] Sections.
- [ ] Subjects.
- [ ] Class subjects.

# المرحلة 3 — الطلاب وأولياء الأمور

**الحالة: ⬜ لم تبدأ**

- [ ] Student CRUD.
- [ ] `StudentEnrollment`.
- [ ] Parent CRUD.
- [ ] `StudentGuardian`.
- [ ] أبناء ولي الأمر.
- [ ] ملف الطالب.
- [ ] التاريخ الأكاديمي.

اكتملت APIs القراءة الأساسية اللازمة للتطبيق ضمن Sprint 1، أما CRUD الكامل فيبقى ضمن هذه المرحلة.

# المرحلة 4 — المعلمون والتكليفات

**الحالة: ⬜ لم تبدأ**

- [ ] Teacher CRUD.
- [ ] `TeacherAssignment` CRUD.
- [ ] تكليفات المعلم الحالية.
- [ ] فصول المعلم.
- [ ] طلاب المعلم.
- [ ] مواد المعلم.

اكتملت APIs القراءة الخاصة بالمستخدم الحالي ضمن Sprint 1، أما CRUD الكامل فيبقى ضمن هذه المرحلة.

# المرحلة 5 — الحضور

**الحالة: ✅ مكتملة**

- [x] Attendance APIs.
- [x] Bulk attendance.
- [x] Daily report.
- [x] Student summary.
- [x] Class summary.
- [x] صلاحيات المعلم.

# المرحلة 6 — الاختبارات والنتائج

**الحالة: ⬜ لم تبدأ**

- [ ] ExamType APIs.
- [ ] Exam APIs.
- [ ] ExamResult APIs.
- [ ] Bulk results.
- [ ] Approval.
- [ ] Bulk approval.
- [ ] Result logs.
- [ ] Student results.
- [ ] Parent child results.

# المرحلة 7 — الواجبات

**الحالة: ✅ مكتملة (Sprint 4A)**

- [x] Homework وmultiple attachments.
- [x] HomeworkSubmission وmultiple attachments.
- [x] Draft/Publish/Close وDraft/Submit/Return/Grade.
- [x] Bulk publish/close/grade الذري.
- [x] Teacher, student and parent views.
- [x] Audit وAdmin وreports وOpenAPI.

# المرحلة 8 — الإعلانات والإشعارات

**الحالة: ⬜ لم تبدأ**

- [ ] Announcement.
- [ ] Notification.
- [ ] Read notification.
- [ ] Read all.
- [ ] Firebase لاحقًا.
- [ ] Email لاحقًا.
- [ ] WhatsApp لاحقًا.

# المرحلة 9 — الجدول الدراسي

**الحالة: ⬜ لم تبدأ**

- [ ] SchoolDay.
- [ ] TimeSlot.
- [x] Timetable period/configuration foundation (Sprint 4.7).
- [x] TimetableEntry linked to TeacherAssignment (Sprint 4.7).
- [x] Student and linked-parent timetable APIs (Sprint 4.7).
- [x] Teacher Today/Week/Current/Next APIs (Sprint 4.7).
- [x] Class Grid, atomic bulk/validate/copy APIs (Sprint 4.7).

# المرحلة 10 — التقارير

**الحالة: ⬜ لم تبدأ**

- [ ] Student reports.
- [ ] Attendance reports.
- [ ] Exam reports.
- [ ] Transcripts.
- [ ] PDF.
- [ ] Excel.
- [ ] Printing.

# المرحلة 11 — لوحات التحكم

**الحالة: ⬜ لم تبدأ**

- [ ] School Admin Dashboard.
- [ ] Teacher Dashboard.
- [ ] Parent Dashboard.
- [ ] Student Dashboard.

# المرحلة 12 — Flutter

**الحالة: 🟡 قيد التنفيذ**

- [x] Flutter foundation.
- [x] Login.
- [x] JWT storage.
- [x] API client.
- [x] Routing.
- [x] Role-based placeholder shells.
- [ ] Teacher app.
- [ ] Parent app.
- [ ] Student app.

# المرحلة 13 — خصائص SaaS

**الحالة: 🔵 مخطط لها لاحقًا**

- [ ] Subscriptions.
- [ ] Plans.
- [ ] School limits.
- [ ] Billing.
- [ ] Super Admin Dashboard.
- [ ] Custom branding.
- [ ] Subdomains.
- [ ] Backups.
- [ ] General Audit Trail.
- [ ] Localization.

# خطة الـ Sprints

## Sprint 1 — الأساس والمصادقة

**الحالة: ✅ مكتملة**

- [x] Auth APIs.
- [x] Current user.
- [x] Permissions.
- [x] API error format.
- [x] Student read APIs.
- [x] Teacher read APIs.
- [x] Parent children API.
- [x] Multi-Tenant tests.

## Sprint 2 — الحضور

**الحالة: ✅ مكتملة**

## Sprint 2.5 — Infrastructure, Quality, Filters & Admin UX

**الحالة: ✅ مكتملة**

- [x] API versioning وOpenAPI.
- [x] Filters موحدة وHealth checks.
- [x] Logging وSecurity وThrottling.
- [x] Admin UX وعزل المدارس.
- [x] CI وRuff وCoverage foundation.
- [x] التحقق النهائي والتسليم: 130 اختبارًا ناجحًا وتغطية 90%.

## Sprint 3 — الاختبارات والنتائج

**الحالة: ✅ مكتملة**

- [x] Exam Types وExams وExam Results CRUD.
- [x] Bulk grade entry ذري.
- [x] Submit/Approve/Reject/Reopen workflow.
- [x] Audit trail وvisibility حسب الدور.
- [x] Student/Parent/Teacher results والتقارير.
- [x] OpenAPI وAdmin و44 اختبار Sprint.
- [x] بوابة التحقق النهائية: 176 اختبارًا وتغطية 92% وOpenAPI سليم.

## Sprint 4 — Homework, Announcements & Notifications

### Sprint 4A — Homework, Submissions & Attachments

**الحالة: ✅ مكتملة**

- [x] Workflows والمرفقات والتقارير والتدقيق وAdmin.
- [x] 285 اختبارًا وOpenAPI نظيف.
- [x] ربط hooks مع Notifications الفعلية في Sprint 4B.


### Sprint 4D — Multi-School Identity & Context

**الحالة: ✅ مكتملة ومتحقق منها**

- [x] هوية User عالمية وSchoolMembership لكل مدرسة ودور.
- [x] Active Context صريح وHistorical Context للقراءة فقط.
- [x] تاريخ الطالب متعدد المدارس ونقل ذري مقيد بـsuper_admin.
- [x] أولياء أمور ومعلمون متعددو المدارس والأدوار مع عزل كامل.
- [x] migration 0020 واختبارات السياق والقيود والنقل.

المرحلة التالية بعد اعتماد Sprint 4C: Architecture Freeze V1 ثم Flutter Foundation.

#### Sprint 4D.1 — Multi-School Consistency Hardening

**الحالة: ✅ مكتملة بعد التحقق**

- [x] تقوية migration 0020 ضد stale legacy schools.
- [x] خدمات مزامنة موحدة للطالب وولي الأمر والمعلم.
- [x] تحقق نقل الطالب وLegacy pointers.
- [x] Historical Homework وتقليل last_used_at writes.
- [x] حماية request-local compatibility adapter.
- [ ] إزالة الاعتماد على request.user.school/role/academic_year تدريجيًا، وتحويل كل الكود إلى Active Context قبل التجميد النهائي لطبقة Flutter.
### Sprint 4B — Notifications, Messaging & School Inbox

**الحالة: ✅ مكتملة ومثبتة في Commit `99a8f53`**

- [x] Notifications معزولة حسب SchoolMembership.
- [x] Homework completion وdashboards.
- [x] المحادثات والرسائل والمرفقات.
- [x] School Inbox وTeacher Broadcast.
- [x] Privacy hardening وMigration 0022.
- [x] 533 اختبارًا ناجحًا وتغطية 93%.

### Sprint 4C — Announcements & Targeting

**الحالة: 🟡 منفذة في شجرة العمل وتنتظر التحقق النهائي**

- [x] Draft/Publish/Close/Archive workflow.
- [x] استهداف المدرسة والأدوار والصف والشعبة والتكليف والطلاب.
- [x] Membership-scoped delivery/read receipts.
- [x] Safe attachments وAdmin وOpenAPI-ready APIs.
- [x] Notifications بعد Commit.
- [x] Inquiry يفتح محادثة منفصلة وآمنة.
- [ ] تشغيل فحص Windows/PostgreSQL الكامل وتثبيت Commit مستقل.

### Architecture Freeze V1

**الحالة: ⬜ بعد اعتماد Sprint 4C**

- [ ] `ARCHITECTURE_FREEZE_V1.md`
- [ ] `API_CONTRACT_V1.md`
- [ ] `FLUTTER_UI_CONTRACT_V1.md`
- [ ] إزالة أي اعتماد جديد على Legacy request.user context قبل Flutter freeze.

## Sprint 5 — Flutter Foundation

**الحالة: ✅ Sprint 5A مكتملة ومقبولة**

### Sprint 5B.0 — Student Design System + Offline Local Foundation

**الحالة: ✅ مكتملة ومقبولة**

- [x] Design tokens، components، RTL، SafeArea، responsive Student shell placeholders.
- [x] Tajawal/Cairo/Noto Sans Arabic bundled offline مع preference مستمرة.
- [x] Drift/SQLite schema v1 في app-private storage لنفس قاعدة Android/iOS.
- [x] عزل cache حسب local user + membership + academic year + resource.
- [x] Atomic replacement، historical metadata، invalidation، logout/session-expiry purge.
- [x] Offline read/repository/data-state foundation واختبارات العزل والسياق والrollback.
- [x] Android debug build + physical Samsung SM N986U launch/login/foundation smoke.
- [ ] iOS native verification على macOS/Xcode (بوابة مستقلة؛ لا تمنع قبول architecture على Windows).

Final decision: **SPRINT 5B.0 DESIGN & OFFLINE FOUNDATION ACCEPTED — READY FOR STUDENT HOME & TIMETABLE**. أول feature-level offline acceptance (online load → offline cached read → online refresh) إلزامي في Sprint 5B.1 عند توفر Student Home/Timetable data فعلية.

### Sprint 5B.1 — Student Home + Timetable + Real Local Cache

**الحالة: ⛔ التنفيذ والقبول الوظيفي ناجحان؛ Nano visual QA مفقود**

- [x] Student Home وToday/Week/Current/Next typed APIs.
- [x] Drift schema v2 وreal timetable cache المعزول.
- [x] Feature-level offline acceptance: online load → offline cached display → online refresh.
- [x] Samsung physical-device flow و25/25 tests وdebug APK.
- [ ] إرفاق Nano Banana references وإكمال side-by-side visual QA.

Current decision: **SPRINT 5B.1 STUDENT HOME & TIMETABLE REJECTED — FIXES REQUIRED** بسبب غياب صور المرجع البصري فقط؛ لا يبدأ Homework.

### Student cache sequence

- Sprint 5B.2: Homework/details/attachment metadata/local draft.
- Sprint 5B.3: Results + Attendance cache.
- Sprint 5B.4: Notifications + Announcements + Conversations read cache.

## Sprint 4.6 — Demo Data + Real E2E Acceptance

**الحالة: ✅ مكتملة ومقبولة**

- [x] Management Command آمن وحتمي وقابل لإعادة التشغيل/reset محدود.
- [x] بيانات مدرستين وسياقات multi-school وhistorical مترابطة.
- [x] اختبارات API E2E للسياق والأدوار والعزل وIDOR.
- [x] بوابات Full Core/Coverage/OpenAPI/Live Server النهائية: 590 tests، Coverage 93%.

## Sprint 4.7 — Timetable & Daily Schedule

**الحالة: ✅ مكتملة ومقبولة في شجرة العمل؛ تنتظر Commit مستقل**

- [x] Config/Periods/TimetableEntry وربط WHEN/WHERE بـTeacherAssignment.
- [x] Grid وBulk/Validate وCopy Day/Week.
- [x] Today/Week/Current/Next للمعلم والطالب وولي الأمر.
- [x] Sprint 4.7.1: Daily Attendance semantics، role-safe shortcut، mutation guards، final-state validation وpreview/save parity.
- [x] بوابات القبول: 609 اختبارًا، Coverage 93%، Ruff/Django/OpenAPI ناجحة.
- [ ] إنشاء Commit Timetable المستقل.

## Sprint 6 — Flutter Teacher

**الحالة: ⬜ لم يبدأ**

## Sprint 7 — Flutter Parent and Student

**الحالة: ⬜ لم يبدأ**

# المسار القصير الحالي

لا يتغير ترتيب التنفيذ الحالي:

`Sprint 4.7.1 → Commit Timetable → Backend UX Contract V1 → Teacher UI Freeze V1 → Sprint 5 Flutter`

لا يبدأ أي عنصر أدناه ضمن Sprint 4.7.1؛ كلها **Deferred / Future** فقط.

# Deferred / Future Roadmap

## بعد Sprint 4.7.1 مباشرة

### 1. Backend UX Contract V1

- [ ] تحديث/إعادة بناء `BACKEND_UX_CONTRACT_V1.md` و`BACKEND_UX_CONTRACT_REPORT.md` من الكود الفعلي بعد Timetable.
- [ ] توثيق API → Role → State → Permission → UI وتحديد Supported / Planned / Not Allowed.
- [ ] اعتماد Timetable كميزة Supported فعليًا.

### 2. Teacher UI Final Review

- [ ] مقارنة تصميم Nano Banana مع Backend UX Contract وتثبيت `TEACHER UI FREEZE V1`.
- [ ] كل شاشة لها مهمة رئيسية واحدة، دون حشو معلومات أو dashboard مزدحم.

### 3. Sprint 5 — Flutter Foundation

- [ ] Project structure وArabic-first RTL وDesign System وtypography/colors/components.
- [ ] Responsive layout وحالات Loading/Empty/Error/Offline.
- [ ] Role routing/navigation وSecure Storage وAPI client وenvironment configuration.

### 4. Flutter Authentication & Active Context

- [ ] JWT login/refresh/logout-blacklist و`auth/me` و`auth/contexts`.
- [ ] `X-School-Membership-ID` و409 `context_required` وتبديل السياق.
- [ ] active/historical/suspended/ended وinactive school وsession expired.
- [ ] Historical read-only UI.

### 5. Flutter Student App

- [ ] تنفيذ `STUDENT UI FREEZE V1`: Home وTimetable Today/Current/Next/Week.
- [ ] Homework/submission lifecycle وResults وAttendance.
- [ ] Notifications وAnnouncements وMessaging وHomework discussion وSchool Support وAcademic history.

### 6. Flutter Parent App

- [ ] تثبيت وبناء `PARENT UI FREEZE V1` مع multiple children عبر مدارس متعددة وchild context.
- [ ] Timetable وAttendance وHomework monitoring وpublished results وupdates.
- [ ] Notifications وTeacher conversations المرتبطة بالطفل وSchool Support وAnnouncements والسجلات التاريخية.

### 7. Flutter Teacher App

- [ ] Multi-school context وTeacher Home وCurrent/Next/Today/Weekly timetable.
- [ ] Attendance والطلاب ضمن TeacherAssignment.
- [ ] Homework create/publish/close وsubmission review/grade/return.
- [ ] Exams وresult entry وsubmit/returned correction.
- [ ] Messaging وparent conversation المرتبطة بالطالب وhomework discussion وbroadcast.
- [ ] Notifications وAnnouncements وhistorical teaching context.

## School Admin Web Portal

### 8. School Admin Web Portal

- [ ] واجهة Web مدرسية مستقلة؛ Django Admin ليس واجهة العميل.
- [ ] Dashboard بسيط للطلاب والأولياء والمعلمين والسنوات والصفوف والشعب والمواد والتكليفات.
- [ ] Attendance oversight ونتائج/اعتماد/نشر وHomework وAnnouncements وSchool Inbox وTimetable Grid وSettings.

### 9. School Onboarding Wizard

- [ ] School profile ثم academic year/classes/sections/subjects/teachers/students/parents/assignments.
- [ ] Review وGo Live بأقل عدد عملي من الخطوات.

### 10. Excel Import Center

- [ ] ImportJob/staging وXLSX templates/upload/column mapping/validation/preview.
- [ ] Row errors وduplicate detection وatomic import حيث يناسب وerror export.
- [ ] استيراد الطلاب والأولياء والمعلمين والصفوف/الشعب والمواد والتكليفات.
- [ ] Timetable import لاحقًا؛ لا كتابة مباشرة إلى production tables دون validation.

## Platform Owner / SaaS Control Plane

### 11. Platform Owner Control Plane

- [ ] فصل Platform Owner/Admin/Support معماريًا عن SchoolMembership.
- [ ] عقد مستقل مناسب مثل `/api/platform/v1/` لإدارة المدارس وonboarding والتفعيل/التعليق والمقاييس والمديرين والتدقيق.
- [ ] Controlled impersonation/support access؛ لا يعتمد Platform Owner على `User.school`.

### 12. Subscription Management

- [ ] SubscriptionPlan وSchoolSubscription وحالات Trial/Active/Grace/Past Due/Suspended/Cancelled.
- [ ] Dates/limits/entitlements/renewal وmanual payment عند الحاجة وسياسة تعليق تلقائي لاحقًا.
- [ ] لا تحذف بيانات المدرسة عند تعليق الاشتراك.

### 13. Parent / Student App Subscription

- [ ] Entitlement مستقل عن School SaaS subscription وعن الرسوم الدراسية إذا اعتمد دفع ولي الأمر.
- [ ] تحديد Free/Paid قبل التنفيذ؛ لا تعطيل SchoolMembership بسبب اشتراك التطبيق.

## Timetable Future Enhancements

### 14. Cross-School Teacher Conflict Warning

- [ ] تحذير privacy-safe لا يكشف المدرسة الأخرى أو تفاصيلها ولا يكسر multi-school support.

### 15. School Calendar / Exceptions

- [ ] Holidays وsuspended days وtemporary schedules وexam days وexceptional replacement lessons.
- [ ] لا ينفذ قبل تصميم School Calendar مستقل.

### 16. Bell-Time Versioning

- [ ] Versioned period schedule يحفظ تاريخ تغير الأوقات داخل السنة بدل تغيير العرض التاريخي القديم.

### 17. Rooms

- [ ] `SchoolRoom` ومنع room conflicts فقط عند ظهور حاجة فعلية؛ النص الحالي كافٍ.

### 18. Templates

- [ ] Suggested period/copy timetable templates دون فرض أوقات عالمية.

### 19. Timetable Excel Import

- [ ] يمر عبر Import Center ويعيد استخدام Bulk/Validate مع Preview قبل الكتابة.

### مؤجلات Timetable ظهرت فعليًا في Sprint 4.7/4.7.1

- [ ] تعريف اختيار صريح عند دعم أكثر من TeacherAssignment حالي لنفس المادة في target class (co-teaching) بدل subject-only copy mapping.
- [ ] تقوية ضمانات conflict/validity إذا أضيفت write paths جديدة؛ جميع الكتابات المستقبلية يجب أن تمر بالخدمة المعتمدة ولا تتجاوز final-state validation.

## Architecture Technical Debt

### 20. Remove Legacy User Context Dependency

- [ ] ترحيل production code تدريجيًا من `request.user.school/role/academic_year` إلى Active Context canonical fields.
- [ ] لا Search/Replace أعمى؛ تمرير context values صراحة إلى services حيث يمكن.
- [ ] إزالة request-local legacy projection فقط بعد اكتمال الترحيل.

### 21. Legacy Fields Removal — Future Major Migration

- [ ] إزالة `User.school` و`User.role` و`User.academic_year` وlegacy domain school fields لاحقًا.
- [ ] لا حذف قبل اكتمال Flutter/API migration واختبارات backward compatibility.

### 22. Account Merge / Advanced Identity

- [ ] Duplicate account merge وSSO وschool-local codes وdual approval لنقل الطالب.

## Production Readiness

## Sprint 5A — Flutter Foundation, Authentication & Active Context

**Status: accepted; ready for Student App**

- [x] Flutter feature-first foundation in `mobile_app/`.
- [x] JWT login/logout, secure token storage, and single-flight refresh.
- [x] Membership-aware Active Context selection and historical read-only mode.
- [x] Arabic RTL Student/Parent/Teacher placeholder shells.
- [x] Windows Developer Mode/symlink environment issue resolved.
- [x] Flutter doctor, pub get, analyze, and 7/7 tests pass.
- [x] Real Demo API smoke remains accepted: `demo_teacher_multi`, 2 contexts, scoped `auth/me`, `RUNSERVER_COUNT=0`.
- [x] Dependency versions preserved; available updates are not an acceptance failure.

Decision: **SPRINT 5A FLUTTER FOUNDATION ACCEPTED — READY FOR STUDENT APP**.

## Sprint 5B.0–5B.2 — Student Foundation, Timetable & Homework

**Status: accepted; ready for Results & Attendance**

- [x] Cross-platform Student design/offline foundation with bundled Arabic fonts, RTL, SafeArea, and scoped Drift cache.
- [x] Student Home plus Today/Week/Current/Next with real offline timetable acceptance.
- [x] Student Homework list/detail and backend-derived completion states/permissions.
- [x] Drift schema v3 Homework list/detail cache and user/membership/year/homework-scoped Local Draft.
- [x] Online-only final submit with draft preservation on failure and deletion only after server confirmation.
- [x] Physical Samsung online/offline/restart/recovery/final-submit E2E.
- [x] Nano Student Homework visual review and responsive 150% coverage.
- [ ] Attachment viewer integration and file-cache LRU/retention policy; metadata/download only is accepted in 5B.2.
- [ ] Native iOS gate remains pending macOS/Xcode.

Decision: **SPRINT 5B.2 STUDENT HOMEWORK ACCEPTED — READY FOR RESULTS & ATTENDANCE**.

## iOS Native Acceptance Gate

- [ ] macOS + Xcode.
- [ ] `flutter doctor`.
- [ ] Pod/SPM dependency resolution as appropriate for the project's Flutter version.
- [ ] iPhone Simulator test.
- [ ] Physical iPhone test.
- [ ] Offline cache test.
- [ ] Context switching test.
- [ ] Secure storage test.
- [ ] RTL/responsive test, including notch/Dynamic Island/home indicator safe areas.
- [ ] Release/archive validation.

Android and iOS remain targets of the same Flutter application and shared business/cache codebase. No separate iOS application will be created. Windows-host inability to run Xcode is not an Android-only architecture exception and is not, by itself, a Sprint rejection.

## Deferred mobile offline/privacy work

- [ ] Offline Mutation Outbox, write synchronization, conflict resolution, and idempotency keys — require an explicit Backend idempotency contract first.
- [ ] Database encryption — deferred pending a maintained Android+iOS stack compatible with the current SDK plus key-lifecycle review; app-private storage, secure token separation, and logout purge apply now.
- [ ] Biometric/PIN offline privacy enhancement.
- [ ] Attachment file-cache size/LRU cleanup policy.
- [ ] Existing Bell/time timetable future items remain deferred.
- [ ] Android mobile maintenance: align `compileSdk` to 35 before release to remove the `sqlite3_flutter_libs` warning; SDK 35 is installed and the current APK build succeeds on compileSdk 34.


### 23. Production Security

- [ ] Real SECRET_KEY وHTTPS redirect وHSTS وsecure cookies وtrusted proxy.
- [ ] `TRUST_X_FORWARDED_FOR` فقط خلف proxy موثوق، مع سياسات CSRF/CORS وAllowed Hosts.

### 24. Production Storage

- [ ] Object storage وmedia/retention policy وbackups وantivirus/provider integration عند اعتماده.

### 25. External Notification Providers

- [ ] Push عبر Firebase/APNs حسب Flutter، وEmail/SMS/WhatsApp فقط حسب business requirements.
- [ ] Failure isolation بعد transaction commit.

### 26. Scheduled Jobs

- [ ] Scheduled publish إن بقي مطلوبًا، retries للإشعارات، وmaintenance/background tasks خارج request lifecycle.

### 27. Monitoring / Operations

- [ ] Error monitoring وstructured logging وhealth/ready monitoring وaudit review.
- [ ] Backup/restore drills وDB monitoring.

## Design / UX Freezes

### 28. Existing UI References

- [ ] `PARENT UI FREEZE V1` و`STUDENT UI FREEZE V1` معتمدان كمرجع تصميم.
- [ ] اتجاه Teacher البصري معتمد، لكن Final Freeze ينتظر Backend UX Contract.
- [ ] Arabic-first RTL وشاشات task-focused بلا dashboards مزدحمة.
- [ ] Visual mockups ليست مصدر صلاحيات؛ Backend Contract هو مصدر الحقيقة الوظيفية.

# سجل التحديثات

| التاريخ | التغيير | الحالة |
|---------|---------|--------|
| 2026-07-29 | إنشاء Roadmap المشروع وبدء Sprint 1. | 🟡 قيد التنفيذ |
| 2026-07-29 | إكمال Sprint 1: المصادقة والصلاحيات وواجهات القراءة واختبارات العزل. | ✅ مكتملة |
| 2026-07-29 | تقوية دورة المصادقة: refresh آمن، ملكية logout، access قديم، وخصوصية guardians. | ✅ مكتملة |
| 2026-07-29 | إكمال Sprint 2: CRUD الحضور وbulk والتقارير واختبارات العزل. | ✅ مكتملة |
| 2026-07-29 | مراجعة Sprint 2: تثبيت ملخص اليوم والتكليفات الحالية والقيود وsection وتزامن bulk. | ✅ مكتملة |
| 2026-07-29 | بدء Sprint 2.5 للبنية والجودة والفلاتر وتحسين Admin. | 🟡 قيد التنفيذ |
| 2026-07-30 | إكمال Sprint 2.5 والتحقق من 130 اختبارًا وOpenAPI بلا تحذيرات وRuff وتشغيل الخادم. | ✅ مكتملة |
| 2026-07-30 | بدء Sprint 3 لمنصة الاختبارات والنتائج ودورة الاعتماد. | 🟡 قيد التنفيذ |
| 2026-07-30 | إكمال Sprint 3: workflow وتدقيق وbulk وتقارير و176 اختبارًا. | ✅ مكتملة |


## Sprint 3.5 - Result publication

**Status: completed**

- [x] Separate approval from publication without changing workflow states.
- [x] Atomic publish of Approved results with skipped-state summary, plus unpublish.
- [x] Reopen safely unpublishes and audits before returning to Draft.
- [x] Atomic bulk publication across multiple exams.
- [x] Hide unpublished results from students and parents.
- [x] Audit publish/unpublish and expose Django Admin actions.
- [x] Add a notification extension point.
- [ ] Scheduled publication (deferred until a scheduler is introduced).


## Sprint 3.5.1 - Publication hardening

**Status: completed**

- [x] Defer publication notifications with `transaction.on_commit`.
- [x] Harden Admin actions and tenant-safe messages.
- [x] Add defensive data repair and publication CheckConstraints in migration 0018.
- [x] Make forwarded audit IP trust explicit and disabled by default.
- [x] Join publisher relations in result and audit selectors.

Verification: 219 core tests passed, coverage 93%, Ruff and OpenAPI clean.

| 2026-08-01 | إكمال Sprint 4A: الواجبات والتسليمات والمرفقات والتقارير و285 اختبارًا. | ✅ مكتملة |

| 2026-08-02 | إكمال Sprint 4D: العضويات والسياق والنقل متعدد المدارس مع 341 اختبارًا مستهدفًا. | ✅ مكتملة |

| 2026-08-02 | Completed Sprint 4B: notifications, homework completion, messaging, and School Inbox; 503 tests and 93% coverage. | Complete |


### Sprint 4B.1 - Communication Privacy & Consistency Hardening

**Status: completed and committed in `99a8f53`**

- [x] One-parent private conversations and pairwise homework discussions.
- [x] School Support creation notifications after commit.
- [x] Atomic attachment batches and support transitions.
- [x] Precise transition audit events.
- [x] Broadcast route whitelist and recursive payload validation.
- [x] Specialized messaging authorization services.
- [x] Preserve the original Migration 0021 and place hardening constraints in Migration 0022.
- [x] Complete Windows/PostgreSQL verification after applying 0022: 533 tests, 93% coverage.


## Student V1 — Homework submission modes

- [x] Backend homework submission mode: `none`, `text`, `attachment`, `text_and_attachment`.
- [x] Legacy homework defaults to `text` for backward compatibility.
- [x] Student Flutter renders only the controls required by the selected mode.
- [x] Backend validates final submission requirements and blocks electronic submissions for `none`.
- [x] Demo acceptance records for `demo_student_a_01` cover all four modes.
- [ ] Teacher Flutter creation screen will expose the mode selector in Teacher V1.
