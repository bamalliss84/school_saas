# Sprint 3 — Exams & Results Platform

## الحالة

✅ مكتملة بعد اجتياز بوابة التحقق النهائية.

## الهدف

منصة متعددة المدارس لأنواع الاختبارات والاختبارات والنتائج، مع إدخال جماعي
ذري، دورة اعتماد، سجل تدقيق، عرض حسب الدور، وتقارير مجمعة دون signals.

## تغييرات البيانات الضرورية

أضيفت migration `0016` فقط، دون تعديل migrations قديمة:

- `ExamResult.workflow_status`: draft/submitted/approved/rejected.
- `ExamResult.approval_reason`.
- حقول action والحالات القديمة والجديدة وسبب الاعتماد وrequest id وIP وuser
  agent في `ExamResultLog`.
- data migration يحافظ على approvals القديمة بتحويل النتائج ذات
  `approved_by` إلى Approved.

يبقى `ExamResult.status` لوصف حضور الطالب للاختبار، منفصلًا عن حالة الاعتماد.

## Approval Workflow

- المعلم ينشئ الاختبار Draft ويدخل أو يعدل نتائج Draft فقط.
- Submit: Draft → Submitted، ولا يسمح لنتيجة not_graded.
- Approve: Submitted → Approved بواسطة school_admin أو super_admin.
- Reject: Submitted → Draft مع حفظ سبب الرفض، حتى يستطيع المعلم التصحيح.
- Reopen: Approved → Draft بواسطة school_admin أو super_admin.
- Approved read-only حتى Reopen.

## Audit Workflow

كل إنشاء أو تعديل marks/status أو submit/approve/reject/reopen يمر عبر
`core/services/exam_results.py` داخل `transaction.atomic()` وقفل صف عند
التعديل. يسجل السجل القيم القديمة والجديدة، action، المستخدم، الوقت، السبب،
request id، IP وuser agent عندما تتوفر. لا تستخدم signals، وDjango Admin
يستخدم الخدمة نفسها. سجل `ExamResultLog` read-only بالكامل.

## Bulk Policy

`POST /api/v1/exam-results/bulk/` ينفذ update-or-create حسب `(exam,
student_enrollment)` داخل transaction واحدة. يرفض الطلاب المكررين ويتحقق من
التكليف والمدرسة والسنة والفصل والصف والشعبة والمادة ونطاق المستخدم والدرجة.
أي خطأ يمنع جميع الكتابات.

## Visibility

- Draft/Submitted/Rejected: teacher صاحب التكليف، school_admin، super_admin.
- Approved: الأدوار السابقة إضافة إلى الطالب وولي أمره.
- السجلات خارج النطاق ترجع 404، وعدم الدور يرجع 403، وغياب المصادقة 401.

## API

- `GET, POST /api/v1/exam-types/`
- `GET, PATCH, PUT, DELETE /api/v1/exam-types/{id}/`
- `GET, POST /api/v1/exams/`
- `GET, PATCH, PUT, DELETE /api/v1/exams/{id}/`
- `GET, POST /api/v1/exam-results/`
- `GET, PATCH, PUT, DELETE /api/v1/exam-results/{id}/`
- `POST /api/v1/exam-results/bulk/`
- `POST /api/v1/exam-results/{id}/submit/`
- `POST /api/v1/exam-results/{id}/approve/`
- `POST /api/v1/exam-results/{id}/reject/`
- `POST /api/v1/exam-results/{id}/reopen/`
- `GET /api/v1/exam-results/{id}/logs/`
- `GET /api/v1/students/me/results/`
- `GET /api/v1/parents/me/results/`
- `GET /api/v1/teachers/me/results/`
- Student transcript وClass/Subject/Exam summaries تحت
  `/api/v1/exam-results/reports/`.

المسارات نفسها باقية تحت `/api/` للتوافق المؤقت.

## Reports

التقارير المنشورة تحسب Approved فقط، بما في ذلك تقارير الإدارة والمعلم.

تعرض التقارير Average وHighest وLowest وPass/Fail counts وrates وتوزيع
النسب إلى ست شرائح. تعتمد القراءة على selectors المقيدة بالدور وتستخدم
`select_related` وaggregations وpagination دون N+1.

## Admin

تحسنت قوائم Exam وExamResult وExamResultLog بالعلاقات والفلاتر. حقول workflow
والاعتماد read-only في ExamResult Admin، وكل تعديل درجات يمر عبر service.
ExamResultLog لا يقبل add/change/delete.

## Tests

أضيف `backend/core/test_sprint3_exams.py` وفيه 44 اختبارًا لـCRUD وbulk
والاعتماد والرفض وإعادة الفتح والتدقيق والصلاحيات والعزل والتقارير والأداء
وOpenAPI وAdmin والأمن.

## التحقق النهائي

- [x] `manage.py check`: دون مشاكل.
- [x] `check --deploy`: ثلاثة تحذيرات بيئة إنتاج معروفة (HSTS وSSL redirect ومفتاح التطوير).
- [x] migrations check وmigrate: migration 0016 مطبقة ولا تغييرات غير مهاجرة.
- [x] جميع اختبارات core: 176/176 ناجحة.
- [x] Ruff ناجح وCoverage إجمالية 92%.
- [x] OpenAPI صالح دون أخطاء أو تحذيرات.
- [x] runserver بدأ، فُحصت endpoints، أُوقف، والعمليات المتبقية صفر.