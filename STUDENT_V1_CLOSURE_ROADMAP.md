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
| Session / Context / Historical | قوي وموجود | موجود ومختبر | ✅ مغلق تقريبًا | Final cross-feature regression فقط |
| الرئيسية | Timetable APIs موجودة | موجودة فعليًا | ✅ موجود | Smoke نهائي مع Features الجديدة |
| الجدول الدراسي | Today / Week / Current / Next موجودة | موجود كامل + Offline cache | 🟠 Closure | مراجعة UI النهائية + small/150% + Offline smoke |
| الواجبات | قوي جدًا | submission modes + attachments + offline draft | ✅ CLOSED وظيفيًا | Final regression فقط |
| النتائج | نشر + ExamType + Historical | فلترة + Offline + details | 🟠 Closure خفيف | ExamType الديناميكي كمرجع Backend + final UI regression |
| الحضور | موجود ومؤسس | Summary + filters + details + Offline | ✅ CLOSED عمليًا | نقطة وقت تسجيل المتأخر تُراجع فقط إذا كان Backend يرسلها |
| الإشعارات | APIs كاملة | منفذة ضمن Communications V1 RC | 🟠 IMPLEMENTED / TEST PENDING | List/read-all/badge/cache + deep-link dispatcher |
| الإعلانات | APIs كاملة + Read + Attachments | منفذة ضمن Communications V1 RC | 🟠 IMPLEMENTED / TEST PENDING | list/detail/read/attachments/cache/inquiry |
| الرسائل | Conversations/Messages/Read/Attachments موجودة | Bottom tab Placeholder | 🔴 REMAINING | conversation list/detail/send/read/cache/attachments |
| School Support | create/list/detail/reply/status Backend موجود | غير منفذ | 🔴 REMAINING | create request + track status + school replies + cache |
| More / Profile | Profile + Schools + Academic History موجودة | حاليًا Appearance + Logout فقط | 🔴 REMAINING | Profile / Current School / Help / About / More navigation |
| تغيير المدرسة / السجل السابق | Backend + Session foundation موجود | Context Screen موجودة | 🟠 CLOSURE | UX مطابق للتصميم + states + final regression |
| Help / About | لا يحتاج Backend أساسي | غير مكتمل | 🟠 بسيط | Static/product info + help navigation |
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
**Communications V1 Mapping is the active step.**  
No Flutter implementation starts until `COMMUNICATIONS_V1_MAPPING.md` is accepted.
