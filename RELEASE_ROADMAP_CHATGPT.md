# School SaaS — Release Roadmap (ChatGPT Execution Track)

Baseline: `bc18562` — Sprint 5B.2 accepted before Phase 0.

## المبدأ الواحد

**ثبّت الأساس → أكمل تدفقًا واحدًا → اختبره على جهاز حقيقي → اعتمده كنقطة رجوع → انتقل لما بعده.**

لا إعادة تصميم، لا تغيير مفاهيم الأعمال المعتمدة، لا إعادة هيكلة واسعة، ولا إضافة Feature خارج نطاق المرحلة قبل إغلاق بوابة القبول الخاصة بها.

## ميثاق التنفيذ الذاتي

عند تنفيذ أي مرحلة: أتعامل مع آخر نسخة معتمدة كمرجع وحيد، أقرأ التدفق كاملًا قبل التعديل، أحافظ على `request.active_membership / active_school / active_role / active_academic_year` كمصدر السياق الرسمي، أحافظ على عزل Drift حسب المستخدم والعضوية والسنة، ولا أغير تصميم Nano المعتمد إلا عند وجود تعارض وظيفي موثق. أصلح السبب الجذري بأقل Patch ممكن، أضيف Regression Test لكل خلل منطقي أصلحه، أشغّل كل الفحوصات المتاحة، أراجع `git diff` ملفًا ملفًا، ولا أعتبر المرحلة مكتملة قبل بوابة قبول واضحة وتجربة Samsung عندما تكون المرحلة Mobile.

## Phase 0 — Mobile Foundation Hardening

الحالة: 🟡 Acceptance جارية — Fix Pack A منفذ بعد نتائج المحاكي، بانتظار إعادة الفحص.

النطاق:
- [x] منع stale membership من تلويث login/context-control requests.
- [x] جعل Backend context-control endpoints مستقلة عن stale membership header.
- [x] Session bootstrap/restore من JWT المخزن.
- [x] التحقق من membership المخزن واستبعاده إذا لم يعد صالحًا.
- [x] حفظ membership بعد نجاح server selection فقط.
- [x] فصل Network offline عن HTTP 401/403/404/409/5xx.
- [x] منع cached homework/timetable من إخفاء رفض صلاحية/سياق من السيرفر.
- [x] Reset لحالة Timetable عند استخدام Bottom Navigation.
- [x] Regression tests للـstale context والـoffline policy.
- [x] Flutter analyze/test قبل Fix Pack A: `No issues found` + `40/40 passed` على بيئة المستخدم.
- [x] Emulator acceptance: restart/session restore.
- [x] Emulator acceptance: user A logout → user B login بدون تسريب.
- [x] Emulator acceptance: online/offline/online recovery.
- [x] Emulator acceptance: timetable navigation.
- [x] Emulator discovery: 403 لا يتحول إلى Offline cache.
- [x] Fix Pack A: Offline cold start من snapshot محلي غير حساس + cache.
- [x] Fix Pack A: Offline indicator موحد عند فشل الشبكة.
- [x] Fix Pack A: stale membership revalidation + تنظيف context + UX عربي آمن.
- [x] Fix Pack A: Bottom Navigation يعيد الواجبات/النتائج إلى root بدل stale details.
- [x] Fix Pack A: تغيير الخط لا يعيد إنشاء Router ولا يقفز للرئيسية.
- [x] Fix Pack A: compileSdk=35 لمتطلب sqlite3_flutter_libs.
- [ ] إعادة `build_runner / flutter analyze / flutter test` بعد Fix Pack A.
- [ ] إعادة Emulator acceptance للإصلاحات الخمسة.
- [ ] expired access token refresh (مؤجل بطلب المستخدم).

## Phase 0 — Acceptance Fix Pack B

الحالة: 🟡 منفذ برمجيًا — بانتظار Flutter/emulator acceptance.

- [x] إصلاح تطبيق الخط على جميع TextTheme styles بدل أجزاء من الواجهة فقط.
- [x] تغيير الخط عبر Theme داخلي بدون إعادة بناء MaterialApp/Router أو القفز للرئيسية.
- [x] توحيد Offline banner بمصدر session واحد وإزالة banner المحلي من Results/Homework/Timetable.
- [x] انتظار revalidation عند 403 قبل عرض الخطأ، والتمييز بين stale membership وfeature permission.
- [x] رسالة stale membership: `هذا الحساب المدرسي غير متاح حالياً`.
- [x] الحفاظ على Offline cache وفق آخر membership تم التحقق منها؛ تغير حالة العضوية على السيرفر لا يمكن اكتشافه أثناء انقطاع الشبكة حتى عودة الاتصال.
- [ ] Flutter analyze/test على بيئة Flutter.
- [ ] Emulator acceptance: font stays on More and changes all text.
- [ ] Emulator acceptance: exactly one offline banner.
- [ ] Emulator acceptance: online suspended membership invalidates current context without stale cache.

## Phase 1 — Student Results

الحالة: 🟡 منفذة برمجيًا — Phase 0 ما زالت معلقة وتُقبل معها في جولة Samsung القادمة.

- [x] تثبيت Student Result API contract: score / total / percentage / dates / feedback.
- [x] تقييد current view بالسنة الدراسية النشطة.
- [x] Published results only عبر Backend scope + دفاع Flutter.
- [x] Flutter list/detail + term/subject filters مطابق لمفهوم Nano بدون إعادة تصميم.
- [x] Drift read cache + offline cached/empty/error states.
- [x] Historical context read-only.
- [x] Regression/model tests مضافة.
- [ ] Flutter analyze/test على بيئة Flutter.
- [ ] Samsung acceptance للـResults Online/Offline/Empty/Error/Detail/Feedback.
- [ ] Phase 0 Samsung acceptance ما زالت معلقة وتنفذ في نفس الجولة.

## Phase 2 — Student Attendance

- Current academic year by default.
- Summary/history/detail.
- present/absent/late/excused.
- لا نضيف check-in time في MVP إلا إذا ثبتت حاجة العمل له.
- Drift read cache + historical read-only.
- Tests + Samsung acceptance.

## Phase 3 — Student Communications

- Notifications.
- Announcements.
- Messages/Conversations.
- Tenant/context isolation tests.
- Offline read strategy حيث يلزم.

## Phase 4 — Student More/Profile

- Profile + school/year/class context.
- Academic history.
- Appearance/settings.
- Logout/context UX.
- Student V1 Final Acceptance.

## Phase 5 — Pilot RC1

- Production configuration gate.
- School Admin Web عبر Django Admin المحسن للـPilot.
- مدرسة Demo واقعية.
- مدرستان لاختبار tenant isolation.
- Student V1 على Samsung.
- Backup/migration/deployment checklist.

## Phase 6 — Parent V1 / Pilot RC2

إعادة استخدام الأساس والواجهات المقروءة: Child Selector → Home → Results → Attendance → Homework → Announcements/Notifications → Messages → More/Profile.

## Phase 7 — Teacher V1 / Pilot RC3

Teacher Today → Attendance bulk entry → Homework lifecycle → Results/grade entry → Communications. نعيد استخدام Backend الحالي ولا نبني Backend موازيًا.

## Deferred until first pilots

Web dashboard تجاري جديد، Billing/Plans، HR/Payroll، buses، LMS متقدم، online exams، AI، والتقارير الثقيلة. لا تدخل قبل إثبات الاستخدام مع المدارس.
