# School SaaS Roadmap

- **المشروع:** School SaaS
- **تاريخ آخر تحديث:** 2026-07-30
- **المرحلة الحالية:** المرحلة 6 — الاختبارات والنتائج
- **Sprint الحالي:** Sprint 4 — الواجبات والإعلانات (جاهز للبدء)
- **نسبة التقدم التقريبية:** 65%
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

**الحالة: ⬜ لم تبدأ**

- [ ] Homework.
- [ ] HomeworkSubmission.
- [ ] Submission.
- [ ] Grading.
- [ ] Teacher, student and parent views.

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

## Sprint 4 — الواجبات والإعلانات

**الحالة: ⬜ لم يبدأ**

## Sprint 5 — Flutter Foundation

**الحالة: ⬜ لم يبدأ**

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
