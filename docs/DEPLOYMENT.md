# دليل التشغيل الفعلي (Release 1.0.1)

هذا الدليل لتشغيل المنصة على خادم Linux واحد باستخدام Docker. كل الأسرار تأتي من ملف `.env.production` على الخادم، ولا تُحفظ في الكود.

## 1. المتطلبات

- خادم Linux (Ubuntu 22.04 أو أحدث): 2 معالج، 4GB ذاكرة، 40GB قرص كبداية.
- Docker وDocker Compose v2.
- اسم نطاق (مثل `school.example.com`) وشهادة HTTPS. أسهل طريق: Caddy أو nginx على الخادم أمام المنصة، أو موازن أحمال من مزود الاستضافة.
- خدمة بريد SMTP لرسائل استعادة كلمة المرور.

## 2. الإعداد أول مرة

```bash
git clone <repo> school_saas && cd school_saas
cp .env.production.example .env.production
nano .env.production   # املأ كل القيم الفارغة
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
docker compose -f docker-compose.prod.yml --env-file .env.production exec backend python manage.py createsuperuser
```

- `DJANGO_ENV=production` يجعل الخادم **يرفض البدء** إذا بقي المفتاح السري الافتراضي، أو كان DEBUG مفعّلًا، أو لم تُضبط أسماء النطاق أو كلمة مرور قاعدة البيانات أو خدمة البريد.
- خدمة `migrate` تطبّق الـ migrations وتجمع الملفات الثابتة مع كل إصدار، ثم يبدأ `backend`.
- `web` يستمع على المنفذ `WEB_PORT` (الافتراضي 8080). وجّه HTTPS إليه، ومرّر الترويسة `X-Forwarded-Proto: https`.

## 3. HTTPS

1. شغّل HTTPS واختبر كل أسماء النطاق.
2. بعد التأكد، ارفع `SECURE_HSTS_SECONDS` إلى `31536000` وأعد تشغيل `backend`.

لا تفعّل HSTS قبل أن يعمل HTTPS، لأن المتصفحات تحفظه.

## 4. النسخ الاحتياطي

```bash
chmod +x scripts/backup_db.sh scripts/restore_db.sh
crontab -e
# 0 2 * * * cd /path/to/school_saas && ./scripts/backup_db.sh >> backups/backup.log 2>&1
```

- يحفظ نسخة يومية مضغوطة في `backups/` ويحذف النسخ الأقدم من 14 يومًا (`KEEP_DAYS`).
- **انسخ مجلد `backups/` خارج الخادم** (تخزين سحابي أو خادم آخر). نسخة على نفس الخادم لا تحمي من فقدانه.
- ملفات المدارس المرفوعة (الشعارات والمرفقات) في وحدة التخزين `media`؛ انسخها احتياطيًا أيضًا.
- جرّب الاسترجاع مرة كل شهر على خادم تجريبي: `./scripts/restore_db.sh backups/<file>.dump`.

## 5. التحديث لإصدار جديد

```bash
git pull
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

خذ نسخة احتياطية قبل كل تحديث.

## 6. المراقبة

- فحص الحياة: `GET /health/live/`، والجاهزية (قاعدة البيانات): `GET /health/ready/`.
- اربطهما بخدمة مراقبة (مثل UptimeRobot) لتنبيهك عند التوقف.
- السجلات: `docker compose -f docker-compose.prod.yml logs -f backend web`.

## 7. قائمة قبل أول مدرسة

- [ ] `.env.production` مكتمل، والمفتاح السري عشوائي وطويل.
- [ ] HTTPS يعمل، ثم HSTS.
- [ ] رسالة استعادة كلمة المرور تصل فعلًا (جرّب من صفحة "نسيت كلمة المرور").
- [ ] النسخ الاحتياطي اليومي يعمل، ونسخة خارج الخادم، واسترجاع مجرّب.
- [ ] مراقبة `/health/ready/`.
- [ ] مراجعة قانونية لصفحتي الشروط والخصوصية (`/terms` و`/privacy`) للسوق المستهدف.
- [ ] حساب Super Admin بكلمة مرور قوية.

## 8. ما ليس في 1.0.1

- إشعارات الجوال الفورية (Push) تحتاج مشروع Firebase ومفاتيحه.
- رسائل SMS تحتاج مزود رسائل وحسابًا.
- بوابة الدفع الإلكتروني مؤجلة؛ الدفع يُسجَّل يدويًا في 1.1.
