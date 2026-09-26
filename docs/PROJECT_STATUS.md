# حالة المشروع

**آخر مزامنة مع `main`:** 2026-09-26

تستخدم هذه الوثيقة الحالات التالية بدقة: **مغلق — مقبول وقت التشغيل**،
**مدمج**، **قيد العمل**، **مخطط**، و**مؤجل**.

  المجال                 المرحلة                            الحالة
  ---------------------- ---------------------------------- -------------
  Shared Backend         Active Context / memberships       معتمد
  School Admin Backend   BE-1 Academic Domain APIs          مكتمل
  School Admin Web       Classes / Sections / Subjects      مكتمل
  School Admin Web       W10 Exams & Results                مدمج
  School Admin Web       Incremental result publishing      مدمج
  School Admin Web       School Admin Web Portal V1         قيد العمل
  Student Mobile         Student Mobile V1                  مغلق
  Student Mobile         Smart Student Home                 مغلق
  Teacher Backend        M2-BE                              مغلق
  Teacher Mobile         M2.1 Shell & Context               مغلق
  Teacher Mobile         M2.2 Timetable                     مغلق — مقبول وقت التشغيل
  Teacher Mobile         M2.3 Assignments + Lesson Roster   مغلق — مقبول وقت التشغيل
  Teacher Mobile         M2.4 Attendance                    مغلق — مقبول وقت التشغيل
  Teacher Mobile         M2.5 Homework                      مغلق — مقبول وقت التشغيل
  Teacher Mobile         M2.6 Exams & Results               مغلق — مقبول وقت التشغيل
  Teacher Mobile         M2.7 Communications                مغلق — مقبول وقت التشغيل

## ملاحظة

الترقيم أعلاه هو الترقيم الحالي المعتمد. الترقيم القديم الذي كان يفصل
Submissions ثم يزيح Exams وCommunications لم يعد صالحًا.

يفتح `TeacherShell` شاشة `TeacherWorkCenterScreen`، وهي تضم
`TeacherHomeworkScreen` وتجربة Exams/Results.

تدعم اتصالات المعلم الإشعارات ودورة حياة الإعلانات ومحادثات
Teacher → Student. إنشاء محادثة Teacher → Parent **مؤجل** إلى حين توفر
اكتشاف آمن لمستلمي أولياء الأمور/الأوصياء ضمن نطاق المعلم؛ ولا تُعد معرفات
العضوية الخام حلًا مقبولًا.

Student Mobile V1 مغلق. إصلاحات ترشيح نتائج الطالب وعرضها مدمجة، مع الحفاظ
على دلالة ظهور النتائج المعتمدة والمنشورة.

يبقى تقييم/إعادة تصميم UI/UX للموبايل والويب مسار عمل رسميًا لـ Release 1.0
بعد استقرار المعالم الوظيفية، دون تغيير قواعد العمل أو عقود API المعتمدة.
