# Backend Overview

Backend هو المصدر المشترك للويب والموبايل.

## Active Context

السلطة الجديدة: `active_membership`, `active_school`, `active_role`,
`active_academic_year`.

## نماذج محورية مؤكدة من الكود

AcademicYear, SchoolMembership, ClassSubject, StudentEnrollment,
TeacherAssignment, SchoolTimetableConfig, SchoolPeriod, TimetableEntry,
AcademicTerm.

## عقود Teacher المهمة المؤكدة

-   `/api/v1/teachers/me/profile/`
-   `/api/v1/teachers/me/assignments/`
-   `/api/v1/teachers/me/assignments/<assignment_id>/students/`
-   `/api/v1/teachers/me/classes/`
-   `/api/v1/teachers/me/students/`
-   `/api/v1/teachers/me/subjects/`
-   `/api/v1/timetable/today/`
-   `/api/v1/timetable/week/`
-   `/api/v1/timetable/current/`
-   `/api/v1/timetable/next/`
-   attendance APIs
-   homework/submission APIs
-   exam-result APIs

راجع `API_CONTRACTS.md` قبل بناء عميل جديد.
