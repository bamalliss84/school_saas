# Phase 0 — Mobile Foundation Hardening Report

Baseline: `bc18562`.

## قبل الاتفاق

Student V1 كان مقبولًا حتى Sprint 5B.2 Homework، مع Timetable وHomework/Drift يعملان على Samsung. المراجعة كشفت stale membership بعد إعادة login، عدم وجود session restore عند restart، offline fallback واسعًا يخفي أخطاء HTTP، وحالة Timetable navigation مؤقتة.

## ما تم بعد الاتفاق

1. Login جديد يمسح session credentials/context القديمة قبل طلب login، لمنع حساب سابق من تلويث الحساب الجديد.
2. ApiClient لا يرسل membership header إلى login/refresh/logout/contexts/default-context.
3. Backend authentication يتجاهل membership header في context-control endpoints كدفاع إضافي؛ stale header لا يمنع اكتشاف السياقات أو تغيير default context أو logout.
4. أضيف Session bootstrap: إذا وجدت JWTs، يكتشف السياقات أولًا، يتحقق من membership المخزن، يمسحه إذا صار stale، يختار سياقًا صالحًا، ثم يستعيد user/session.
5. ContextRepository لا يحفظ membership محليًا إلا بعد نجاح server selection للسياق النشط.
6. أضيفت سياسة Offline موحدة: cache fallback فقط لأخطاء النقل/الاتصال؛ HTTP authorization/context/server errors لا تتحول إلى Offline.
7. Homework detail/list وTimetable طُبقت عليها السياسة الجديدة.
8. Bottom Navigation يعيد Home من Timetable إلى الحالة الصحيحة بدل إبقاء `showTimetable` عالقًا.
9. أضيفت Regression tests للـoffline classification، عدم fallback على 403، وstale membership context-control في Backend.
10. أضيف Release Roadmap مستقل يحكم المراحل القادمة بمبدأ واحد.

## المتبقي لقبول Phase 0

- تشغيل Flutter formatter/analyze/tests على بيئة فيها Flutter SDK.
- تجربة Samsung: restart restore، تبديل الحساب، stale membership، offline/online، token refresh.
- إذا نجحت البوابة: تثبيت Phase 0 كنقطة رجوع ثم Phase 1 Results فقط.
