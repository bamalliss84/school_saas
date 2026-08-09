# School SaaS Roadmap

- **المشروع:** School SaaS
- **تاريخ آخر تحديث:** 2026-08-01
- **المرحلة الحالية:** المرحلة 7 — الواجبات
- **Current sprint:** Sprint 4B - Context-Aware Notifications, Homework Completion, Messaging & School Inbox (complete)
- **نسبة التقدم التقريبية:** 72%
- **آخر Commit مرجعي معروف:** `7e80ffe Sprint 2.5: harden infrastructure filters and admin UX`

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
- [ ] Timetable.
- [ ] TimetableEntry.
- [ ] Student timetable.
- [ ] Teacher timetable.
- [ ] Class timetable.

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

**الحالة: ⬜ لم تبدأ**

- [ ] Flutter foundation.
- [ ] Login.
- [ ] JWT storage.
- [ ] API client.
- [ ] Routing.
- [ ] Role-based home.
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

**الحالة: ⬜ لم يبدأ**

## Sprint 4.6 — Demo Data + Real E2E Acceptance

**الحالة: ✅ مكتملة ومقبولة**

- [x] Management Command آمن وحتمي وقابل لإعادة التشغيل/reset محدود.
- [x] بيانات مدرستين وسياقات multi-school وhistorical مترابطة.
- [x] اختبارات API E2E للسياق والأدوار والعزل وIDOR.
- [x] بوابات Full Core/Coverage/OpenAPI/Live Server النهائية: 590 tests، Coverage 93%.

## Sprint 6 — Flutter Teacher

**الحالة: ⬜ لم يبدأ**

## Sprint 7 — Flutter Parent and Student

**الحالة: ⬜ لم يبدأ**

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
