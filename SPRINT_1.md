# Sprint 1 — الأساس والمصادقة

## الهدف

تأسيس المصادقة والصلاحيات وعزل المدارس وواجهات القراءة الأساسية التي يحتاجها تطبيق Flutter، دون تغيير الموديلات أو تنفيذ CRUD كامل للطلاب أو المعلمين.

## APIs المنفذة

| Method | Endpoint | الوظيفة |
|---|---|---|
| POST | `/api/auth/login/` | إصدار access وrefresh مع معلومات المستخدم الحالي. |
| POST | `/api/auth/refresh/` | تجديد access بعد إعادة التحقق من المستخدم والمدرسة. |
| POST | `/api/auth/logout/` | إدراج refresh token في blacklist بعد التحقق من ملكيته للمستخدم الحالي. |
| GET | `/api/auth/me/` | معلومات المستخدم والمدرسة والسنة والملف المرتبط. |
| GET | `/api/students/` | قائمة الطلاب ضمن النطاق مع pagination وبحث وترتيب وفلترة. |
| GET | `/api/students/{id}/` | تفاصيل الطالب ضمن نطاق المستخدم. |
| GET | `/api/students/me/profile/` | ملف الطالب المرتبط بالمستخدم الحالي. |
| GET | `/api/students/{id}/academic-history/` | تاريخ قيود الطالب من الأحدث إلى الأقدم. |
| GET | `/api/parents/me/children/` | أبناء ولي الأمر وروابطهم وقيودهم الحالية. |
| GET | `/api/teachers/me/assignments/` | تكليفات المعلم مع دعم `?current=true`. |
| GET | `/api/teachers/me/classes/` | الصفوف والشعب الفريدة للمعلم. |
| GET | `/api/teachers/me/students/` | الطلاب الفريدون ضمن التكليفات الحالية. |
| GET | `/api/teachers/me/subjects/` | المواد الفريدة ضمن التكليفات الحالية. |

المسارات السابقة لـ JWT وقائمة المدارس بقيت متوافقة.

## الصلاحيات والعزل

- `super_admin` يرى الطلاب في جميع المدارس.
- `school_admin` يرى طلاب مدرسته فقط.
- `teacher` يرى الطلاب ذوي القيد الحالي المطابق لتكليفاته الحالية في المدرسة والسنة والصف والشعبة.
- `parent` يرى أبناءه المرتبطين عبر `StudentGuardian` فقط.
- `student` يرى سجله فقط.
- المستخدم دون مدرسة لا يرى بيانات مدرسة، باستثناء `super_admin`.
- جلب طالب بواسطة ID يبدأ من queryset المسموح، ولذلك يعاد 404 خارج النطاق.
- endpoints الخاصة بالمعلم وولي الأمر والطالب تعيد 403 للدور غير المناسب.
- كل API محمية تستخدم `IsActiveSchoolUser`، لذلك يُرفض access token القديم بـ403 إذا عُطل الحساب المدرسي أو المدرسة.
- الطالب لا يرى قائمة guardians؛ الأدوار الإدارية والمعلم ضمن نطاقه وولي الأمر للطفل المرتبط يمكنهم رؤيتها.

## أمثلة

### Login

```json
{
  "username": "teacher",
  "password": "password"
}
```

```json
{
  "access": "...",
  "refresh": "...",
  "user": {
    "id": 1,
    "username": "teacher",
    "full_name": "Teacher",
    "email": "",
    "phone": null,
    "role": "teacher",
    "school": {"id": 1, "name": "School A"},
    "academic_year": {"id": 1, "name": "2026"},
    "linked_profile": {"teacher_id": 1}
  }
}
```

يرفض Login المستخدم غير النشط أو `is_active_school_user=False` والمستخدم المرتبط بمدرسة غير نشطة.

### Logout

```json
{"refresh": "refresh-token"}
```

الاستجابة الناجحة `205 Reset Content`. يتحقق Logout أولًا أن claim `user_id` يخص المستخدم الحالي؛ التوكن المختلف يُرفض دون إدراجه في blacklist، وبعد الإلغاء الصحيح يفشل استخدام الرمز نفسه للتجديد.

### خطأ موحد

```json
{
  "success": false,
  "message": "Not found.",
  "errors": {}
}
```

### Student list

```text
GET /api/students/?page=1&page_size=20&search=Ahmed&ordering=full_name&is_active=true
```

الحجم الافتراضي 20، ويمكن تغييره عبر `page_size` حتى 100.

## تشغيل الاختبارات

```text
backend\venv\Scripts\python.exe backend\manage.py check
backend\venv\Scripts\python.exe backend\manage.py makemigrations --check --dry-run
backend\venv\Scripts\python.exe backend\manage.py test core
```

## Migrations

- لم تتغير `models.py`.
- لم تنشأ migration داخل `core`.
- أضيف `rest_framework_simplejwt.token_blacklist` إلى التطبيقات.
- طُبقت migrations الرسمية للمكتبة حتى `0013` على قاعدة التطوير.

## الحالات المؤجلة

- CRUD الكامل للطلاب وأولياء الأمور ضمن المرحلة 3.
- CRUD الكامل للمعلمين والتكليفات ضمن المرحلة 4.
- APIs الحضور والاختبارات والنتائج في Sprints لاحقة.
- OpenAPI/versioning وتوسيع filtering لبقية القوائم.
- عزل Django Admin حسب المدرسة ما زال مؤجلًا.

## معايير القبول والنتيجة الفعلية

- [x] Login وRefresh متوافقان مع SimpleJWT.
- [x] Logout يبطل refresh token فعليًا.
- [x] Current User يعيد الملف المرتبط حسب الدور.
- [x] أخطاء API موحدة مع أكواد HTTP صحيحة.
- [x] القوائم تستخدم Pagination موحدة.
- [x] APIs الطلاب وولي الأمر والمعلم مطبقة.
- [x] عزل المدرسة والدور والوصول المباشر مطبق.
- [x] `manage.py check` ناجح.
- [x] فحص migrations ناجح: `No changes detected`.
- [x] 42 اختبارًا مكتشفًا و42 ناجحًا، تشمل حالات تعطيل الحساب والمدرسة وملكية refresh وخصوصية guardians.
- [x] السيرفر بدأ دون أخطاء، أعاد 401 منسقة لمسار محمي، ثم أُوقف.

**حالة Sprint 1: ✅ مكتملة**