# School SaaS — Agent Rules

## Source of Truth

- الفرع `main` في المستودع الرسمي هو المرجع المعتمد للمشروع.
- GitHub هو نقطة التزامن بين جميع أدوات ووكلاء التطوير.
- لا يعتمد أي Agent على worktree قديم باعتباره أحدث نسخة دون مقارنة Git.
- أي عمل جديد يتم في Branch/Worktree مستقل ثم يراجع قبل دمجه في `main`.

## Architecture

لا يوجد Backend مستقل للويب وBackend مستقل للموبايل.

جميع العملاء يستخدمون:

Web / Mobile
→ Shared Backend API
→ Shared Database

ولا يجوز إنشاء منطق Backend خاص بعميل معين إذا كان العقد المشترك كافيًا.

## Active Context

مصدر السلطة في الكود الجديد هو:

- `request.active_membership`
- `request.active_school`
- `request.active_role`
- `request.active_academic_year`

ولا يعتبر:

- `request.user.school`
- `request.user.role`
- `request.user.academic_year`

مصدر سلطة للكود الجديد، ويستخدم فقط عند الحاجة إلى Legacy Compatibility.

## Tenant Isolation

كل قراءة أو كتابة يجب أن تحترم المدرسة الموجودة في Active Context.

ممنوع:

- Cross-school data leakage
- الاعتماد على IDs يرسلها العميل دون التحقق من ملكيتها للسياق النشط
- تجاوز Tenant Isolation من Web أو Mobile أو API

## Historical Context

السياق التاريخي Read-only.

يسمح بعرض البيانات التاريخية حسب الصلاحيات.

يمنع إنشاء أو تعديل أو حذف البيانات التشغيلية داخل سنة تاريخية إلا إذا نص عقد معتمد صراحة على خلاف ذلك.

## Academic Model

- `Subject` على مستوى المدرسة حسب العقد الحالي.
- `ClassSubject` يمثل علاقة المادة بالصف.
- `ClassSubject` لا يمثل المعلم.
- `TeacherAssignment` هو علاقة التدريس التشغيلية.
- `StudentEnrollment` هو مصدر انتماء الطالب الأكاديمي للسنة/الصف/الشعبة.

لا تخلط بين هذه الكيانات.

## Backend Changes

لا يعدل Backend إلا عند:

1. وجود Contract Gap مثبت.
2. عدم وجود Endpoint/Service مشترك يحقق الحاجة.
3. تحديد أثر التعديل على Web وMobile.
4. إضافة أو تحديث الاختبارات اللازمة.

لا ينشأ Endpoint خاص بالموبايل أو الويب لتجاوز عقد مشترك قائم.

## Development Workflow

كل Milestone يتبع:

Contract
→ Tests
→ Implementation
→ Regression
→ Review
→ Commit
→ Merge

لا تسجل أي ميزة `Completed` قبل نجاح الاختبارات والمراجعة.

## Git Safety

ممنوع استخدام:

`git add .`

بشكل أعمى.

قبل أي Commit:

- راجع `git status`.
- Stage الملفات المقصودة فقط.
- لا تحذف أو تعمل reset لتغييرات غير مرتبطة.
- لا تنظف Worktree قبل التأكد من عدم وجود عمل غير محفوظ.
- لا تعمل merge/cherry-pick لفرع كامل إذا كانت هناك commits غير مرتبطة.

## Agent Responsibilities

ChatGPT:
- الإشراف المعماري.
- تحديد العقود والنطاق.
- مراجعة النتائج والاختبارات.
- إدارة خطة Release 1.0.
- مراجعة Git/GitHub قبل الدمج.

Claude Code:
- تنفيذ المهام المحلية المحددة.
- كتابة الاختبارات والكود ضمن النطاق المكلف به.
- عدم توسيع Scope دون موافقة.
- تقديم تقرير بالملفات والاختبارات والـdiff قبل الدمج.

لا يعمل وكيلان على نفس الملفات في الوقت نفسه دون تنسيق صريح.

## Documentation

بعد اعتماد كل Slice:

- Mobile يحدث `mobile_app/docs/`.
- Web يحدث `web_portal/docs/`.
- Backend يحدث `backend/docs/` عند تغيير العقد.
- الوثائق المركزية تحدث بعد الدمج عند الحاجة.

الكود والعقد والاختبارات المعتمدة هي المرجع عند تعارض وثيقة قديمة معها.