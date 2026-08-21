# Backend UX Contract V1

Baseline: `565f672 Sprint 4.7: add timetable daily schedule and integrity hardening`

هذا الملف هو مصدر الحقيقة الوظيفي لتصميم Flutter. ترتيب الثقة: production code، ثم الاختبارات الناجحة وAPI routing/schema، ثم الوثائق. التصاميم المرئية لا تمنح صلاحيات.

## 1. Classification

- `SUPPORTED_NOW`: العقد الحالي يستخدم Active Context مباشرة ومغطى في الكود الحالي.
- `SUPPORTED_WITH_LEGACY_COMPATIBILITY`: الميزة مدعومة، لكن جزءًا من مسارها القديم يقرأ `request.user.school/role/academic_year` بعد إسقاط Active Context عليها داخل الطلب فقط.
- `PLANNED_BACKEND_GAP`: مطلوب مستقبلًا ولا يوجد له عقد backend حالي.
- `NOT_ALLOWED`: محظور في العقد الحالي؛ يجب إخفاؤه من UI.

## 2. Canonical context and session

المفاهيم الرسمية هي `request.active_membership`, `request.active_school`, `request.active_role`, و`request.active_academic_year`. يرسل العميل JWT و`X-School-Membership-ID` لكل school API. `GET auth/contexts/` يعرض العضويات، access mode، السنة، وعدادات unread؛ `GET auth/context/` يعرض السياق الحالي؛ `POST auth/context/default/` يغير الافتراضي صراحة.

حالات `SchoolMembership`:

| State | UX |
|---|---|
| `active` | `read_write` بحسب الدور والصلاحية |
| `historical` | `read_only`; يسمح فقط بـGET وبعلامات القراءة الشخصية للإشعارات/المحادثات/الإعلانات |
| `suspended`, `ended` | `unavailable`; لا تفتح واجهة المدرسة |
| school inactive | `unavailable` |

إذا كان للمستخدم أكثر من سياق active ولم يرسل header، يرجع `409 context_required`: افتح Context Selection ثم أعد الطلب. تغيير المدرسة يغير كل queries/badges/navigation. لا تخلط البيانات بين السياقات.

`User.school/role/academic_year` ليست مفاهيم UX. هي توافق تقني مؤقت لبعض endpoints القديمة ولا تُحفظ من request-local projection.

## 3. Role contracts

### Student

- Screens: Context/School history، profile، Today/Current/Next/Week timetable، homework lifecycle، published results، attendance summary، notifications، announcements، direct messages/homework discussions، School Support.
- Reads: سجله فقط؛ enrollment في المدرسة/السنة المختارة؛ إعلانات وإشعارات ومحادثات membership الخاصة به.
- Writes: draft/edit/attachments/final-submit لتسليمه عندما تسمح flags؛ بدء teacher-student/homework/support conversation؛ messages/read markers؛ announcement inquiry/read.
- Forbidden: إدارة attendance، timetable، exams/results، homework definitions، broadcasts، recipients، أو أي طالب آخر.
- Historical: academic history وtimetable وhomework المسلّم له وبيانات context-scoped المسموحة؛ لا submission mutation. تبقى personal read markers فقط.
- Multi-school: هوية واحدة، لكن يوجد active student membership واحد؛ المدارس السابقة تظهر كسياقات historical.
- Hide: كل admin/teacher CTA وattendance shortcut (`can_take_attendance=false`).

### Parent

- Screens: children، child schools/history، child timetable، attendance، homework monitoring، published results، notifications، announcements، teacher conversations، homework discussion، School Support.
- Reads: الأطفال المرتبطون فقط؛ كل request خاص بطفل يتحقق من `StudentGuardian` والمدرسة المختارة.
- Writes: محادثة مع معلم مرتبطة بطفل وتكليف صالح؛ homework discussion؛ support؛ messages/read markers؛ announcement inquiry/read.
- Forbidden: تعديل بيانات الطفل الأكاديمية، attendance، homework/submission، results، timetable، أو اختيار guardian آخر كمشارك.
- Historical: سجل الطفل ومدرسته السابقة وجدوله وواجباته المسموحة للقراءة؛ لا عمليات أكاديمية. personal read markers مسموحة.
- Multi-school: يمكن أن يكون الأطفال في مدارس مختلفة؛ اختر SchoolMembership ثم child داخلها. لا تجمع مدارس متعددة في شاشة بيانات واحدة.
- Hide: attendance action، grading، publishing، broadcast، admin controls.

### Teacher

- Screens: multi-school context، Today/Current/Next/Week، assigned students/classes/subjects، daily attendance، homework/submissions، exams/results entry، messages، parent/student/homework conversations، broadcast، notifications، announcements.
- Reads: `TeacherAssignment` الحالية التابعة للمعلم في المدرسة/السنة المختارة فقط، وما يتفرع منها.
- Writes: attendance ضمن assignment؛ homework create/update draft/publish/close والgrading/return؛ exams/results draft/bulk/submit؛ authorized conversations/messages؛ assignment-scoped broadcast؛ own-assignment announcements.
- Forbidden: approve/reject/reopen/publish/unpublish results؛ timetable administration؛ targeting another teacher؛ group chat/free recipient search؛ School Inbox administration.
- Historical: timetable والتعليم السابق context-scoped للقراءة؛ لا attendance/homework/result/broadcast/announcement mutation. personal read markers فقط.
- Multi-school: كل مدرسة membership مستقل؛ لا يعرض أو يكشف تعارض مدرسة أخرى.
- Hide: Admin approval/publication، Timetable Grid edit، support assignment/status، cross-school details.

### School Admin

- Screens: school-scoped students/teachers/assignments، attendance oversight، exams/result approval/publication، homework oversight، announcements، School Inbox، Timetable Config/Periods/Grid.
- Reads/Writes: موارد المدرسة والسنة المختارة فقط؛ timetable CRUD/bulk/copy، exam types، approve/reject/reopen/publish/unpublish، announcements، support assignment/status/reply، teacher-assignment broadcast.
- Forbidden: أي مدرسة أخرى، Platform Owner actions، أو تجاوز validation/tenant scope.
- Historical: historical membership لا يكتب؛ أخفِ كل mutation. القراءة تبقى في النطاق الذي تسمح به endpoint.
- Multi-school: membership منفصل لكل مدرسة؛ لا لوحة cross-tenant.

### Super Admin

- هو دور backend حالي ضمن school context، ويمكنه نطاقات الإدارة الحالية عندما يوجد/يُختار سياق مدرسة صالح.
- يمكنه student transfer وعمليات approval/publication والإدارة التي تسمح بها APIs الحالية.
- ليس Platform Owner ولا يمنحه العقد الحالي Control Plane أو subscriptions أو controlled impersonation.
- بدون `active_school/active_academic_year` لا تفترض أن school APIs قابلة للاستخدام؛ UI يجب أن يطلب سياقًا مناسبًا.

## 4. Timetable — `SUPPORTED_NOW`

المبدأ المعماري: `TeacherAssignment = WHO / WHAT / WHOM`، و`TimetableEntry = WHEN / WHERE`. Break هو `SchoolPeriod` للعرض ولا يملك teaching entry.

| Role | Supported timetable UX | Writes |
|---|---|---|
| Teacher | Today، Week، Current، Next، own multi-school/historical schedule | لا timetable writes؛ attendance shortcut فقط عند السماح |
| Student | Today، Week، Current، Next حسب enrollment في السياق | لا |
| Parent | linked child Today/Week؛ child مختلف بعد اختيار مدرسته | لا |
| School/Super Admin | Config، Periods، Entries، Grid، Bulk، Validate، Copy Day/Week، Assignment Options | نعم في active writable context |

Primary APIs: `timetable/today|week|current|next/`, `config/`, `periods/`, `entries/`, `grid/`, `bulk/`, `validate/`, `copy-day/`, `copy-week/`, `assignment-options/`.

الحالات الزمنية: `finished`, `current`, `upcoming`. Next يبحث حتى 14 يومًا. Grid final-state validation يطبق clears منطقيًا قبل upserts؛ preview وsave لهما feasibility واحدة. Used working day لا يُحذف، وused lesson period لا يتحول إلى break ولا يُحذف.

### Attendance shortcut

هو Daily Attendance للصف/الشعبة/التاريخ، وليس per-period:

- `not_recorded`: صفر سجلات للطلاب المتوقعين.
- `partial`: بعض الطلاب فقط.
- `recorded`: العدد المسجل بلغ العدد المتوقع.
- الحقول: `attendance_count`, `attendance_expected_count`, `attendance_status`.
- `can_take_attendance=true` فقط للمعلم المالك، في writable active context، لتاريخ اليوم، ولحصة current/upcoming ضمن صلاحية assignment.
- Student/Parent/Admin/Historical: false.

## 5. Homework — `SUPPORTED_WITH_LEGACY_COMPATIBILITY`

### Homework workflow

`draft → published → closed`. Draft فقط قابل للتعديل والمرفقات؛ published يقبل التسليم؛ closed لا يقبل تسليمًا جديدًا. Teacher يملك assignment الخاص به؛ School Admin/Super Admin ضمن نطاقهما. Bulk publish/close ذري.

### HomeworkSubmission workflow

`draft → submitted → graded` أو `submitted/graded → returned → submitted`. Student ينشئ/يعدل draft أو returned ويضيف/يحذف مرفقاته ثم final-submit. Teacher يعيد submitted/graded، ويقيّم submitted فقط، منفردًا أو bulk. Parent يراقب ولا يكتب.

### Derived completion

`graded`, `returned`, `submitted`, `draft`, `closed_without_submission`, `overdue`, `not_started`. اعتمد flags من API: `can_create_draft`, `can_edit`, `can_final_submit`; لا تعيد اشتقاق الصلاحية في Flutter.

Historical student/parent homework قراءة فقط؛ flags الكتابة false. لا تعرض teacher mutations في historical context.

## 6. Exams and results — `SUPPORTED_WITH_LEGACY_COMPATIBILITY`

- Exam states: `draft`, `published`, `closed`, `cancelled`.
- Result academic status: `not_graded`, `present`, `absent`, `excused`, `exempted`.
- Result workflow: `draft → submitted → approved`; reject يعيد submitted إلى `draft` مع reason؛ reopen يعيد approved إلى `draft` ويفك publication أولًا إن لزم.
- Approved لا تعني Published. Publication مستقلة عبر `is_published/published_at/published_by`، وتشمل approved results فقط.
- Teacher: create/update/bulk grade في scope، submit for approval، وتصحيح returned/rejected draft. لا approve/reject/reopen/publish/unpublish.
- School/Super Admin: approve/reject/reopen وpublish/unpublish وbulk publish، إضافة إلى management scope.
- Student/Parent: لا يرون إلا `workflow_status=approved` و`is_published=true` في own/child result views.
- Audit logs تسجل create/update/submit/approve/reject/reopen/publish/unpublish.

Primary APIs: `exam-types/`, `exams/`, `exam-results/`, `exam-results/bulk/`, workflow actions، publish/unpublish، role result lists والتقارير.

## 7. Attendance — `SUPPORTED_WITH_LEGACY_COMPATIBILITY`

- Daily model: سجل واحد لكل StudentEnrollment في التاريخ، statuses: `present`, `absent`, `late`, `excused`.
- Teacher يكتب ويقرأ فقط assignments والطلاب الحاليين المخولين؛ bulk attendance مدعوم.
- School/Super Admin: oversight في tenant scope.
- Student: own records/summary. Parent: linked children only.
- APIs: list/detail، `attendance/bulk/`, `daily/`, student summary، class summary.
- Historical UI لا يعرض create/update/bulk؛ يعرض فقط records التي يعيدها context-scoped selector. Timetable metadata shortcut لا ينشئ مفهوم period attendance.

## 8. Messaging and School Support — `SUPPORTED_NOW`

الأنواع الوحيدة:

| Type | Who starts / context |
|---|---|
| `teacher_student` | Teacher لطالب في assignment أو Student لمعلم assignment |
| `teacher_parent` | Teacher لولي واحد مرتبط بالطالب، أو Parent لمعلم طفل مرتبط |
| `homework_discussion` | Teacher/Student/Parent حول homework published/closed؛ private pair |
| `school_support` | Student/Parent/Teacher؛ يديره School Admin |

لا group chat ولا free recipient search. Teacher-parent/homework discussions لا تجمع عدة guardians أو student+guardian. Conversation states: `open`, `in_progress`, `resolved`, `closed`; الرسائل ممنوعة في resolved/closed. المشاركون SchoolMembership، والsender membership. Attachments batches validated، reply-to داخل نفس conversation، وread marker لكل participant.

Creator غير الإداري يغلق/يعيد فتح محادثته ضمن transition المسموح؛ School Admin يدير support assignment/status/resolution note/reply. Historical context يسمح قراءة المحادثات وعلامة القراءة الشخصية، لكنه لا يبدأ أو يرسل أو يغير status.

## 9. Teacher Broadcast — `SUPPORTED_NOW`

Broadcast هو إنشاء Notifications جماعية بعد commit، وليس Group Chat. المرسل Teacher أو School Admin؛ النطاق `TeacherAssignment` current في المدرسة، والمعلم يملك assignment. الجمهور: `students`, `parents`, `students_and_parents`، مع optional student subset داخل assignment فقط. الروابط المسموحة: `homework_detail`, `conversation_start`, `school_home` بمعاملاتها المحددة.

## 10. Notifications — `SUPPORTED_NOW`

كل Notification تخص `recipient_membership` واحدًا وتُقرأ داخل سياقه فقط. تدعم list/detail/filter، mark read، mark all، unread count، context badges، وdeduplication per membership/key. الأنواع الحالية تشمل homework/result/message/support/announcement/system. Historical يسمح read markers الشخصية فقط. لا توجد شاشة إرسال حر؛ broadcast endpoint مقيد كما سبق.

## 11. Announcements — `SUPPORTED_NOW`

Workflow: `draft → published → closed`، و`published|closed → archived`. Draft فقط قابل للتحرير والمرفقات. الاستهداف الفعلي: `school`, `roles`, `classroom`, `section`, `teacher_assignment`, `students`; يمكن توسيع classroom/section/assignment/student targets إلى parents وفق القواعد. لا يستقبل client قائمة memberships.

School/Super Admin يديران الاستهداف المدرسي. Teacher ينشئ/يدير فقط announcement الخاص به والمقيد بـown current assignment. Recipients يملكون delivery/read receipt؛ inquiry إن كان متاحًا ينشئ محادثة منفصلة آمنة. Historical يقرأ delivered announcements ويحدّث read marker فقط.

الفرق: Announcement محتوى رسمي one-way مع lifecycle واستهداف وتسليم؛ Teacher Broadcast notification event سريع بلا conversation أو announcement lifecycle.

## 12. Historical UI contract

| Role | Show | Hide |
|---|---|---|
| Student | school/academic history، context timetable، delivered announcements/notifications/conversations، readable historical homework/results/attendance إن أعادتها endpoints | submissions edits، attendance action، inquiries/new messages/support، كل academic writes |
| Parent | linked child schools/history، child timetable، delivered communication، readable child records | child academic mutation، new conversations/support، replies، all staff actions |
| Teacher | own context timetable، assignments/content/communications المتاحة للقراءة | attendance entry، homework/exam/result writes، broadcast، new/reply conversations، announcement management |
| Admin/Super Admin | records التي تسمح endpoint بقراءتها في السياق | كل create/update/delete/workflow actions |

لا تعتمد على disabled button فقط؛ أخفِ mutation controls. إذا ظهر 403 historical بسبب stale UI، اعرض “هذا السياق للقراءة فقط” وحدّث الشاشة.

## 13. Error UX

كل خطأ يستخدم envelope: `success=false`, `message`, `errors`.

| HTTP | UX behavior |
|---|---|
| 400 | اعرض field/structured validation؛ أبقِ المدخلات ولا تعِد الطلب تلقائيًا |
| 401 | امسح session بعد فشل refresh واذهب إلى Login |
| 403 | أخفِ/عطّل action؛ historical = read-only message؛ لا تطلب سياقًا آخر تلقائيًا |
| 404 | “غير موجود أو غير متاح” دون كشف cross-tenant existence |
| 405 | خلل client/route؛ لا تعرض action غير المدعوم |
| 409 | إذا `errors.code=context_required` افتح Context Selection؛ غير ذلك اعرض conflict state |
| 415 | أصلح Content-Type/file request؛ رسالة format غير مدعوم |
| 429 | اعرض rate-limit/retry state مع backoff؛ لا loop فوري |

## 14. Screen/API matrix

| Role | Screen group | Primary API | Context | Mode / state rules |
|---|---|---|---|---|
| All | Login/Context | `auth/*` | optional ثم required | active/read-only/unavailable؛ 409 selector |
| Student | Profile/history | `students/me/*` | mixed | own only؛ history read-only |
| Parent | Children/history | `parents/me/children/*` | mixed | guardian-linked child only |
| Teacher | Assignments/students | `teachers/me/*` | yes | own current assignments |
| Student/Parent/Teacher | Timetable | `timetable/today|week|current|next` | yes | read; teacher shortcut conditional |
| Admin | Timetable Grid | `timetable/config|periods|grid|bulk|validate|copy-*` | writable | final-state validation |
| Roles | Homework | `homework/*`, `homework-submissions/*` | yes | role + workflow flags |
| Roles | Results | `exams/*`, `exam-results/*` | yes | approved != published |
| Roles | Attendance | `attendance/*` | yes | daily; assignment/guardian scope |
| Roles | Messaging | `conversations/*`, `school-inbox/*` | yes | private pairs/support states |
| Roles | Notifications | `notifications/*`, `communication/badges/` | yes | membership-scoped; read markers |
| Roles | Announcements | `announcements/*` | yes | delivery + lifecycle + role flags |

## 15. Teacher UI final checklist

| Capability | Classification | UX rule |
|---|---|---|
| Multi-school context | SUPPORTED_NOW | explicit membership switch |
| Today / Current / Next / Week | SUPPORTED_NOW | own assignments |
| Attendance | SUPPORTED_WITH_LEGACY_COMPATIBILITY | daily; shortcut conditional |
| Students | SUPPORTED_WITH_LEGACY_COMPATIBILITY | within assignment |
| Homework | SUPPORTED_WITH_LEGACY_COMPATIBILITY | draft/publish/close |
| Submissions / Grade / Return | SUPPORTED_WITH_LEGACY_COMPATIBILITY | workflow-gated |
| Exams / Bulk result entry | SUPPORTED_WITH_LEGACY_COMPATIBILITY | own assignment |
| Submit for approval / rejected correction | SUPPORTED_WITH_LEGACY_COMPATIBILITY | teacher allowed |
| Approve / reject / reopen / publish | NOT_ALLOWED | Admin only |
| Messages / parent tied to child | SUPPORTED_NOW | private pair, assignment validated |
| Homework discussion | SUPPORTED_NOW | published/closed homework |
| Broadcast | SUPPORTED_NOW | notification, not group chat |
| Notifications / Announcements | SUPPORTED_NOW | membership/own assignment scope |
| Historical context | SUPPORTED_NOW | reads + personal read markers only |

## 16. Parent UI checklist

Children, multiple schools, child context/history, timetable, attendance, homework monitoring, published results, notifications, messages, School Support, announcements: backend-supported. Attendance/homework/results use legacy compatibility projection internally. Any design that edits child academic data or combines multiple school datasets is `NOT_ALLOWED`.

## 17. Student UI checklist

Current context، academic history، timetable، homework lifecycle، published results، attendance، notifications، private messages/homework discussion، support، announcements، historical mode: backend-supported. Homework/results/attendance remain `SUPPORTED_WITH_LEGACY_COMPATIBILITY`; academic management and cross-student access are `NOT_ALLOWED`.

## 18. Planned gaps only

- `PLANNED_BACKEND_GAP`: Platform Owner/Control Plane and subscriptions.
- `PLANNED_BACKEND_GAP`: customer-facing School Admin Web Portal.
- `PLANNED_BACKEND_GAP`: onboarding wizard and validated Excel Import Center.
- `PLANNED_BACKEND_GAP`: removal of legacy request.user context dependency.
- `PLANNED_BACKEND_GAP`: timetable bell-time versioning, calendar exceptions, privacy-safe cross-school teacher warning, and SchoolRoom/conflicts if required.

هذه gaps لا تمنع Flutter Student/Parent/Teacher foundation إذا التزم التصميم بالعقد والتصنيفات أعلاه.
