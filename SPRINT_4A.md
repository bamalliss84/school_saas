# Sprint 4A — Homework, Submissions & Attachments

**الحالة:** ✅ مكتملة

## النطاق المنفذ

- Homework بحالات Draft وPublished وClosed، مع نشر وإغلاق فردي وجماعي ذري.
- HomeworkSubmission بحالات Draft وSubmitted وReturned وGraded، مع تسليم نهائي وإرجاع وتصحيح فردي وجماعي.
- مرفقات متعددة مستقلة للواجبات والتسليمات، ورفع multipart ذري.
- عزل المدرسة والدور قبل جلب السجل، بحيث يرجع ID خارج النطاق 404.
- تقارير الواجب والطالب والفصل، وحقول Flutter الجاهزة.
- سجل `HomeworkActionLog` دون تخزين الإجابات أو الملفات أو مسارات التخزين.
- Django Admin معزول حسب المدرسة ويستخدم الخدمات في الإجراءات.

## الموديلات وMigration

أضافت Migration `0019_homework_submissions`:

- `Homework`
- `HomeworkAttachment`
- `HomeworkSubmission`
- `HomeworkSubmissionAttachment`
- `HomeworkActionLog`

تشمل القيود تفرد التسليم لكل واجب وقيد طالب، وعدم سلبية الدرجات والأحجام، واتساق تواريخ وحالة نشر الواجب، وmetadata التصحيح.

## المرفقات والأمان

تُضبط الحدود من environment. تتحقق الخدمة من الاسم والحجم والعدد والامتداد وMIME وتوقيعات PDF/JPEG/PNG، وتحظر الامتدادات التنفيذية والخطرة والامتدادات المزدوجة. أسماء التخزين UUID داخل نطاق المدرسة ولا تعتمد على اسم العميل. حذف قاعدة البيانات يسبق حذف Storage الذي يعمل عبر `transaction.on_commit`؛ فشل Storage يسجل بأمان ولا يعيد العملية الأصلية.

## Hooks المستقبلية

`homework_published_hook` و`submission_graded_hook` و`submission_returned_hook` و`antivirus_scan_hook` هي extension points آمنة وبدون إرسال فعلي. تعمل hooks الناتجة عن workflows بعد commit بمعرّفات ثابتة، وسيجري ربطها بمنصة Notifications في Sprint 4C.

## API

المسارات الرسمية تحت `/api/v1/` مع توافق `/api/`، وتشمل CRUD المقيد، إجراءات publish/close/final-submit/return/grade وعمليات bulk، المرفقات، قوائم الطالب وولي الأمر والمعلم، وتقارير summary. جميع عمليات الكتابة محمية بـ`IsActiveSchoolUser` وthrottling scopes مخصصة.

## الاختبارات والتحقق

- 285 اختبار `core` ناجح، منها 66 اختبارًا جديدًا لـSprint 4A.
- OpenAPI عبر `config.schema_urls`: صفر أخطاء وصفر تحذيرات.
- لا توجد Announcements أو Notification models في 4A.