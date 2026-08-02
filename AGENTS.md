# Project

School SaaS متعدد المدارس مبني بـ Django وDjango REST Framework.

# Project root

- جذر المشروع هو `school_saas`.
- مجلد Django هو `backend`.
- البيئة الافتراضية الصحيحة هي:

```text
backend\venv
```

# Core architecture

- النظام Multi-Tenant.
- كل بيانات التشغيل يجب أن تكون معزولة حسب `school`.
- `super_admin` يرى جميع المدارس.
- `school_admin` يرى بيانات مدرسته فقط.
- `teacher` يرى فقط الطلاب والفصول والمواد المرتبطة بتكليفاته.
- `parent` يرى أبناءه فقط.
- `student` يرى ملفه وبياناته فقط.
- لا يجوز تجاوز عزل المدارس حتى لو أُرسل ID مباشر في الرابط.
- عند عدم السماح بالوصول إلى سجل خارج نطاق المستخدم، يفضّل إرجاع 404 بدل كشف وجود السجل.

# Existing concepts that must not be broken

- `Student` لا يحتوي `classroom` أو `academic_year` مباشرة.
- تاريخ الطالب محفوظ في `StudentEnrollment`.
- `TeacherAssignment` يحفظ تكليفات المعلم حسب السنة والفصل والشعبة والمادة.
- `StudentGuardian` يربط ولي الأمر بالطالب.
- `ExamResultLog` يستخدم لتتبع تغييرات نتائج الاختبارات.
- منطق تعديل `ExamResult` وتسجيل التغييرات موجود في:
  `backend/core/services/exam_results.py`
- لا تعِد إنشاء signals لنتائج الاختبارات إلا بقرار معماري صريح.

# Coding rules

- اقرأ الملفات المرتبطة بالمهمة قبل التعديل.
- نفذ أقل تعديل ممكن يحقق المطلوب.
- لا تعِد تصميم المشروع دون طلب صريح.
- لا تغيّر أسماء الموديلات أو الحقول أو العلاقات الحالية دون ضرورة واضحة.
- استخدم `transaction.atomic` للعمليات المركبة التي يجب أن تنجح أو تفشل كوحدة واحدة.
- ضع منطق الأعمال المركب في services بدل تكراره داخل views أو serializers.
- استخدم `select_related` و`prefetch_related` عند الحاجة لتجنب N+1.
- تحقق من `school` و`academic_year` والعلاقات المتقاطعة.
- لا تستخدم `print` داخل كود الإنتاج.
- لا تضع أسرارًا أو كلمات مرور داخل الكود.
- لا تستخدم حلولًا مخفية مثل thread-local لتحديد المستخدم الحالي.
- لا تحذف اختبارات فاشلة لإجبار المهمة على النجاح.

# Migrations

- لا تنشئ migration إلا عند تغيير models فعليًا.
- لا تعدل migration مطبقة سابقًا إلا إذا طُلب ذلك صراحة.
- ملفات migrations ذات الامتداد `.py` يجب أن تبقى متتبعة.
- لا تُتبع ملفات `*.pyc` أو `__pycache__/`.

# Required verification

بعد كل مهمة برمجية نفذ من جذر المشروع:

```text
backend\venv\Scripts\python.exe backend\manage.py check

backend\venv\Scripts\python.exe backend\manage.py makemigrations --check --dry-run

backend\venv\Scripts\python.exe backend\manage.py test core
```

- إذا تغيرت models وكان مطلوبًا إنشاء migration، أنشئها ثم أعد تشغيل فحص migrations والاختبارات.
- إذا فشل أي أمر، أصلح السبب الجذري وأعد جميع أوامر التحقق.
- لا تقل إن المهمة ناجحة دون تنفيذ أوامر التحقق فعليًا.

# Server verification

عند الحاجة فقط:

- شغل السيرفر مؤقتًا باستخدام:

  ```text
  backend\venv\Scripts\python.exe backend\manage.py runserver 127.0.0.1:8000 --noreload
  ```

- تحقق أنه بدأ بدون أخطاء.
- أوقف العملية بعد التحقق.
- لا تترك السيرفر أو أي عملية اختبار تعمل في الخلفية.

# Git safety

- راجع `git status` و`git diff` قبل وبعد المهمة.
- لا تنفذ `git commit` أو `git push` إلا بطلب صريح.
- لا تعدل أو تحذف ملفات خارج جذر المشروع.
- لا تتبع:

  ```text
  .env
  backend/venv
  backend/venvvenv
  __pycache__/
  *.pyc
  db.sqlite3
  backend/media
  backend/school_logos
  ```

# Tests

- أضف اختبارات لكل صلاحية أو سلوك جديد.
- اختبر عزل المدارس.
- اختبر الوصول حسب الدور.
- اختبر الحالات الصحيحة والحالات المرفوضة.
- استخدم اختبارات Django أو DRF `APIClient` بدل الاعتماد فقط على اختبار يدوي للسيرفر.

# Final report

في نهاية كل مهمة أعط تقريرًا يحتوي على:

- الملفات التي تم تعديلها.
- سبب كل تعديل.
- هل أُنشئت migration.
- نتيجة `manage.py check`.
- نتيجة فحص migrations.
- عدد الاختبارات الناجحة.
- هل شُغل السيرفر وأُوقف.
- أي مخاطر أو نقاط متبقية.
- لا تنفذ `commit` أو `push` إلا بطلب صريح.

# Current task workflow

- عند طلبي "نفذ المهمة الحالية"، اقرأ `tasks/CURRENT_TASK.md` بالكامل.
- نفذ المهمة حسب `AGENTS.md`.
- أثناء التنفيذ حدّث `reports/LATEST_REPORT.md` بعد كل مرحلة رئيسية.
- عند الفشل سجّل الأمر الفاشل والخطأ والسبب والإصلاح.
- في نهاية المهمة اكتب التقرير النهائي الكامل في `reports/LATEST_REPORT.md`.
- لا تنفذ `commit` أو `push` إلا إذا نصت المهمة الحالية على ذلك.
- لا تعدل محتوى `tasks/CURRENT_TASK.md` أثناء التنفيذ.
- لا تضع أسرارًا أو tokens أو بيانات شخصية في التقرير.

## Multi-school identity rules (Sprint 4D)

- `User` is a global identity; `SchoolMembership` is the source of school and role authorization.
- The canonical request context for all new code is `request.active_membership`, `request.active_school`, `request.active_role`, and `request.active_academic_year`.
- `request.user.school`, `request.user.role`, and `request.user.academic_year` are temporary Legacy Compatibility Fields only; new code must not use them as authorization sources.
- School APIs require an Active Context. New code must not authorize from `user.school` or `user.role`.
- `StudentEnrollment` is the source of the student's school history; `Student.school` is a legacy current pointer only.
- Teachers may have active memberships and assignments in multiple schools.
- Historical Context is read-only at the server, regardless of client UI.
- Never copy attendance, results, homework, submissions or files during a school transfer.
- Use the shared context helpers and `require_writable_context`; never use thread-local state.

## Sprint 4D.1 — Consistency hardening

- Membership state changes must go through the synchronization services in `core.services.identity`; do not add signals.
- A current active `StudentEnrollment` drives the student's active/default membership and all legacy school/year pointers.
- Guardian changes must resynchronize parent memberships; one other current child keeps the school active.
- Current teacher assignments require an active teacher membership. Derived synchronization never downgrades an explicit active membership.
- `last_used_at` changes only on explicit default-context selection, never on ordinary context GET requests.
- The in-memory user mutation in authentication is request-local compatibility only and must never be saved.
- Historical student/parent Homework access uses the selected historical membership and remains read-only.


## Sprint 4B communication rules

- New communication code must authorize only from `request.active_membership`, `request.active_school`, `request.active_role`, and `request.active_academic_year`; never from legacy `request.user.school/role/academic_year`.
- A Notification belongs to exactly one `recipient_membership`; a Conversation participant and Message sender belong to `SchoolMembership`.
- Never permit cross-school messaging or free recipient search. Resolve recipients from active-context academic relationships.
- Historical contexts are read-only except the documented personal notification/conversation read markers.
- Notification and message side effects run after commit using immutable IDs; do not add signals.


## Sprint 4B.1 hardening rules

- Teacher-parent and homework conversations are private pairs; never place multiple guardians or a student and guardians in one conversation.
- Conversation serializers validate input shape only. Specialized messaging services are the security boundary and must revalidate role, membership, school, academic year, assignment, enrollment, guardian, and reuse policy.
- School Support creation notifications run after commit and contain only a bounded subject preview.
- Attachment batches validate completely under a message lock and clean only files created by the failed batch.
- Support status, timestamps, resolution note, and audit must be one atomic service operation.
- Broadcast actions must use the documented route whitelist and route-specific parameters.
- Notification payload checks must be recursive, depth-limited, size-limited, JSON-native, and reject sensitive keys case-insensitively.
- Never rewrite an already-applied communication migration to add hardening constraints; preserve 0021 and apply the additional guarantees through 0022 or a later forward migration.
