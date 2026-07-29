# Sprint 2.5 — Infrastructure, Quality, Filters & Admin UX

## الهدف

تجهيز Backend School SaaS للتشغيل والتوسع قبل الموسم الدراسي، مع الحفاظ
على عزل المدارس وواجهات Sprint 1 وSprint 2، ودون إضافة Frontend أو تغيير
الموديلات.

## التغييرات

- مسارات versioned جديدة تحت `/api/v1/` مع إبقاء `/api/` للتوافق المؤقت.
- OpenAPI وSwagger وReDoc بواسطة `drf-spectacular`.
- query serializers موحدة للفلاتر والتقارير.
- health liveness/readiness محدودة المعلومات.
- pagination metadata إضافية دون حذف الحقول القياسية.
- throttling قابل للضبط من البيئة.
- logging منظم لا يسجل tokens أو كلمات المرور أو Authorization headers.
- إعدادات أمان وCORS وCSRF وJWT قابلة للضبط من البيئة.
- عزل Django Admin حسب المدرسة وتحسين شاشات الطلاب والحضور.
- GitHub Actions وRuff وCoverage.

## API Versioning

المسار المعتمد للعملاء الجدد هو `/api/v1/`. جميع المسارات القديمة تحت
`/api/` مستمرة مؤقتًا ولا تستخدم Views أو Serializers مكررة. الإيقاف
المستقبلي للمسارات القديمة يحتاج خطة deprecation مستقلة.

## OpenAPI URLs

- `/api/schema/`
- `/api/docs/`
- `/api/redoc/`
- `/api/v1/schema/`
- `/api/v1/docs/`

في التطوير تكون الوثائق متاحة، وعندما يكون `DEBUG=False` تتطلب مستخدمًا
موثقًا و`is_staff=True`. الـschema يولد من مسارات `/api/v1/` فقط حتى لا
تتكرر عمليات التوافق القديم.

## Filters

### Students

`search`, `is_active`, `school_id`, `academic_year_id`, `classroom_id`,
`section_id`, `enrollment_status`, `is_current`, و`ordering`.

البحث يستخدم `full_name` و`student_code`؛ موديل Student الحالي لا يحتوي
حقل phone. لا يستطيع غير super_admin توسيع النطاق بواسطة `school_id`.

### Teacher assignments

`current`, `academic_year_id`, `classroom_id`, `section_id`, `subject_id`,
`date`, و`ordering`. يبقى الـqueryset محصورًا بالمعلم الحالي.

### Attendance

`attendance_date`, `date_from`, `date_to`, `status`, `student_id`,
`student_enrollment_id`, `teacher_assignment_id`, `academic_year_id`,
`academic_term_id`, `classroom_id`, `section_id`, `search`, و`ordering`.

تُرفض المدة المعكوسة والحالات والتواريخ والقيم غير الصحيحة بـ400 منسقة.

### Reports

تستخدم التقارير query serializers مستقلة. لم تتغير سياسة Daily Report:
فلتر status يؤثر على records فقط ولا يغير recorded أو not_recorded.

## Health checks

- `/health/` و`/health/live/`: يثبتان عمل Django دون فحص dependencies.
- `/health/ready/`: ينفذ `SELECT 1` ويتحقق من جدول migrations.
- `/api/v1/health/`: liveness تحت مساحة API.

تعيد readiness حالة 503 آمنة دون أسماء قواعد بيانات أو credentials.

## Logging

يوجد console handler وصيغة موحدة وloggers لـ`django.request`,
`django.security`, `school_saas`, و`core`. المستوى الافتراضي INFO،
ويصبح DEBUG محليًا عند `DEBUG=True`. لا يوجد logging للـrequest bodies أو
headers الحساسة.

## Security

تقرأ الإعدادات الحساسة والتشغيلية من environment، بما فيها SECRET_KEY،
DEBUG، ALLOWED_HOSTS، قاعدة البيانات، CORS، CSRF، JWT lifetimes، HTTPS،
HSTS وthrottle rates. لا يستخدم CORS allow-all. إعدادات HTTPS لا تُفرض
محليًا افتراضيًا.

## Throttling

القيم الافتراضية:

- anon: `1000/hour`
- user: `5000/hour`
- login: `100/hour`
- refresh/logout: `200/hour`
- reports: `1000/hour`
- bulk attendance: `500/hour`
- docs: `300/hour`

كلها قابلة للتعديل من environment، والقيم المحلية مرتفعة لتجنب كسر
الاختبارات.

## Admin UX وعزل المدارس

- Branding عربي وRTL عبر لغة Django العربية.
- دخول Admin محصور في Django superuser أو staff بدور super_admin أو
  school_admin.
- Django superuser وstaff super_admin عالميان.
- staff school_admin يرى مدرسته فقط.
- querysets وforeign keys محصورة حسب المدرسة.
- school_admin لا يستطيع إنشاء مدرسة أو ترقية مستخدم إلى super_admin.
- Attendance Admin يعرض الطالب والمدرسة والسنة والصف والشعبة بكفاءة.
- Student Admin يحمّل القيد الحالي بـPrefetch لمنع N+1.
- ExamResultLog غير قابل للإضافة أو التعديل أو الحذف يدويًا.

لم يُضف theme خارجي أو CSS ضخم أو dashboard مخصص.

## CI

`.github/workflows/backend-ci.yml` يستخدم Python 3.13 وPostgreSQL 16،
ثم ينفذ migrate وcheck وفحص migrations والاختبارات وcompileall وRuff.
بيئة Windows المحلية الحالية تستخدم Python 3.14، بينما 3.13 إصدار مستقر
متاح في GitHub Actions ومتوافق مع Django 6.

## Ruff وCoverage

أضيف `requirements-dev.txt` و`ruff.toml`. أوامر الجودة:

```text
backend\venv\Scripts\python.exe -m ruff check backend/core backend/config
backend\venv\Scripts\python.exe -m coverage run backend/manage.py test core
backend\venv\Scripts\python.exe -m coverage report
```

لا يوجد coverage threshold مرتفع قبل قياس baseline الفعلي.

## التشغيل المحلي

```text
backend\venv\Scripts\python.exe backend\manage.py migrate
backend\venv\Scripts\python.exe backend\manage.py check
backend\venv\Scripts\python.exe backend\manage.py runserver 127.0.0.1:8000 --noreload
```

استخدم `.env.example` مرجعًا ولا تضع الأسرار في Git.

## Static وMedia

`STATIC_ROOT` و`MEDIA_ROOT` محددان. يخدم Django media محليًا فقط عند
`DEBUG=True`. الإنتاج يجب أن يستخدم خادم ملفات أو object storage مستقلًا.
مجلدا media وschool logos يبقيان خارج Git. S3 مؤجل.

## الأعمال المؤجلة

- seed_demo_school لتجنب إدخال بيانات وكلمات مرور تجريبية قبل اعتماد سياسة.
- Admin dashboard مخصص ورسوم بيانية.
- تخزين S3 وCDN.
- قياسات query performance على بيانات إنتاج مماثلة.
- إزالة مسارات `/api/` القديمة بعد خطة deprecation.
- توسيع schema descriptions التفصيلية لبعض serializers المحسوبة.

## معايير القبول

- [x] `/api/v1/` يعمل والمسارات القديمة باقية.
- [x] OpenAPI وSwagger يعملان.
- [x] Filters موحدة وتتحقق من القيم.
- [x] Health checks تعمل.
- [x] Logging وأمان وتشغيل من environment.
- [x] Throttling منسق ومختبر.
- [x] Admin معزول حسب المدرسة.
- [x] CI وRuff وCoverage مضافان.
- [x] بوابة التحقق النهائية مكتملة: نجح 130 اختبارًا، وبلغت التغطية 90%.
- [x] الخادم فُحص وأُوقف دون عمليات متبقية.

## مراجعة OpenAPI والنشر النهائية

قبل المراجعة وُجد 21 تحذيرًا (14 سببًا فريدًا)، وكلها من كود المشروع:
7 حالات لحقول `SerializerMethodField`، و6 querysets جرى تقييمها أثناء توليد
Schema، وتصادم تسمية enum واحد. عولجت بوصف الحقول بـ`extend_schema_field`
وحراسة `swagger_fake_view` و`ENUM_NAME_OVERRIDES` دون تغيير شكل API أو
الصلاحيات. بعد المراجعة: صفر تحذيرات وصفر أخطاء. لم تبق تحذيرات من مكتبة
خارجية أو تحذيرات وصفية تحتاج إلى استثناء.

نجح `check --deploy` مع ثلاثة تحذيرات مقصودة في بيئة التطوير: HSTS غير
مفعّل، وSSL redirect غير مفعل، ومفتاح التطوير الافتراضي غير صالح للإنتاج.
أصبح `DEBUG=False` افتراضيًا، ويجب ضبط HTTPS وHSTS ومفتاح سري حقيقي من
environment عند النشر.

أكدت اختبارات Django Client أن الزائر يحوّل إلى صفحة دخول Admin، وأن
Django superuser وstaff school_admin المصرح لهما يدخلان، بينما أدوار
teacher وparent وstudent ممنوعة حتى مع `is_staff=True`. وتبقى querysets
وForeignKey محصورة بمدرسة school_admin، وExamResultLog غير قابل للتعديل.

**حالة Sprint 2.5: ✅ مكتملة.**
