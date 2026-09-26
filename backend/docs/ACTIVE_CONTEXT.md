# Active Context

كل طلب جديد يجب أن يتعامل مع السياق النشط باعتباره مصدر المدرسة والدور
والسنة.

## Canonical

-   request.active_membership
-   request.active_school
-   request.active_role
-   request.active_academic_year

## Legacy

`request.user.school`, `request.user.role`, `request.user.academic_year`
ليست سلطة للكود الجديد.

## Multi-role

العضوية المختارة تحدد الدور. الحساب نفسه قد يكون Teacher وParent دون
حسابين.

## Historical

السياق التاريخي read-only. الحماية يجب أن تكون Backend policy وليست مجرد
تعطيل زر في الواجهة.
