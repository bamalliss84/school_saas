# School SaaS — Student App V1 Closure Roadmap

**Last reviewed:** 2026-08-21  
**Purpose:** المصدر الرسمي لحالة إغلاق تطبيق الطالب V1. عند إكمال أي بند يجب تحديث هذا الملف بدل الاعتماد على الذاكرة الشفهية فقط.

## Status legend
- ✅ **CLOSED / DONE**: مكتمل ومختبر ولا يُعاد فتحه إلا عند وجود Regression حقيقي.
- 🟠 **CLOSURE**: الأساس موجود؛ المطلوب إغلاق UX/UI/Regression فقط.
- 🔴 **REMAINING**: ما زال يحتاج تنفيذ Flutter فعلي.
- 🟡 **DEFERRED**: ليس مانعًا لإطلاق V1 التجريبي ويمكن تأجيله بقرار واضح.

## Current Student V1 status

| الجزء | Backend | Flutter الحالي | الحالة الحالية | ما بقي للإغلاق |
|---|---|---|---|---|
| Session / Context / Historical | قوي وموجود | موجود ومختبر | ✅ CLOSED | M1.4 Supervisor accepted |
| الرئيسية | Timetable APIs موجودة | موجودة فعليًا | ✅ CLOSED | M1.4 Supervisor accepted |
| الجدول الدراسي | Today / Week / Current / Next موجودة | موجود كامل + Offline cache | ✅ CLOSED | M1.3 Supervisor runtime accepted |
| الواجبات | قوي جدًا | submission modes + attachments + offline draft | ✅ CLOSED | M1.4 Supervisor accepted |
| النتائج | نشر + ExamType + Historical | فلترة + Offline + details | ✅ CLOSED | Runtime state/navigation regression accepted |
| الحضور | موجود ومؤسس | Summary + filters + details + Offline | ✅ CLOSED عمليًا | نقطة وقت تسجيل المتأخر تُراجع فقط إذا كان Backend يرسلها |
| الإشعارات | APIs كاملة | منفذة ضمن Communications V1 | ✅ CLOSED | Supervisor accepted |
| الإعلانات | APIs كاملة + Read + Attachments | منفذة ضمن Communications V1 | ✅ CLOSED | Supervisor accepted |
| الرسائل | Conversations/Messages/Read/Attachments موجودة | list/detail/send/read/cache/attachments | ✅ CLOSED | Supervisor accepted |
| School Support | create/list/detail/reply/status Backend موجود | منفذ ومختبر على Android Emulator | ✅ CLOSED | Supervisor accepted |
| More / Profile | Profile + Schools + Academic History موجودة | Profile / school / history / context / help / about | ✅ CLOSED | M1.2 Supervisor accepted |
| تغيير المدرسة / السجل السابق | Backend + Session foundation موجود | Multi-context + historical read-only | ✅ CLOSED | M1.2 Supervisor accepted |
| Help / About | لا يحتاج Backend أساسي | مكتمل | ✅ CLOSED | M1.4 Supervisor accepted |
| Native Push Firebase/APNs | Extension points موجودة | غير منفذ | 🟡 DEFERRED | يمكن بعد V1 Pilot إذا كانت In-App notifications كافية |

## Official design references
هذه الصور هي **Design Contracts** لتطبيق الطالب. لا يُنسخ منها منطق قديم يخالف قرارًا وظيفيًا أحدث؛ التصميم مرجع بصري، والقرارات الوظيفية المعتمدة لاحقًا لها الأولوية.

- `design/student_v1/student_results_v1.jpg`
- `design/student_v1/student_attendance_v1.jpg`
- `design/student_v1/student_more_profile_v1.jpg`
- `design/student_v1/student_communications_v1.jpg`

### Preserved functional decisions over older mockups
- عرض الدرجات بصيغة `18 من 20` لتفادي RTL بدل `/`.
- ExamType يأتي من Backend ويُعرض ديناميكيًا حسب البيانات المتاحة، ولا نثبت قائمة وهمية داخل Flutter.
- Offline = آخر بيانات حقيقية محفوظة فقط؛ **لا Fake mutations**.
- Cache scope دائمًا حسب User + Membership + Academic Year لمنع اختلاط المدارس/السنوات.
- Historical = read-only domain data؛ personal read markers فقط عندما يسمح Backend بذلك.

## Closure order — shortest path to Pilot
1. **Communications V1** — Notifications + Announcements + Messages + School Support.
2. **More / Profile + Context UX Closure**.
3. **Timetable UI Closure**.
4. **Results final light closure (ExamType + regression)**.
5. **Full Student V1 Regression / Offline / 150% / small-device / RTL**.
6. **Student App V1 Pilot Candidate**.

## Completed milestones
- Phase 0 Foundation: Session / Context recovery / scoped offline foundation — accepted in project testing.
- Homework V1 Contract: submission modes (`none/text/attachment/text_and_attachment`) — accepted.
- Results V1 functional implementation — accepted with ExamType closure note.
- Attendance V1: online filters/details + states + responsive 150% + offline cache — accepted on emulator and tests.

## Current next work
**Student Mobile V1 is ✅ CLOSED / DONE — SUPERVISOR ACCEPTED and ready for school pilot.**
The next official Mobile milestone is **Teacher App V1 / M2**, now unblocked by Student V1 closure; it has not started.
