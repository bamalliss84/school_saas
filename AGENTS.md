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
