from django.db.models import Prefetch, Q

from .models import Student, StudentEnrollment, StudentGuardian, Teacher


def _student_base_queryset():
    enrollments = StudentEnrollment.objects.select_related(
        'academic_year',
        'classroom',
        'section',
    ).order_by('-is_current', '-academic_year__start_date', '-created_at')
    guardians = StudentGuardian.objects.select_related('parent').order_by(
        '-is_primary',
        'id',
    )
    return Student.objects.select_related('school', 'user').prefetch_related(
        Prefetch('enrollments', queryset=enrollments),
        Prefetch('guardians', queryset=guardians),
    )


def students_for_user(user):
    """Scope students by tenant and role before any object lookup."""
    queryset = _student_base_queryset()

    if not user or not user.is_authenticated:
        return queryset.none()

    if user.role == 'super_admin':
        return queryset

    if not user.school_id:
        return queryset.none()

    queryset = queryset.filter(school_id=user.school_id)

    if user.role == 'school_admin':
        return queryset

    if user.role == 'teacher':
        teacher = Teacher.objects.filter(
            user=user,
            school_id=user.school_id,
        ).first()
        if teacher is None:
            return queryset.none()

        assignments = teacher.assignments.filter(
            is_current=True,
            school_id=user.school_id,
        )
        if user.academic_year_id:
            assignments = assignments.filter(
                academic_year_id=user.academic_year_id,
            )

        enrollment_scope = Q()
        for assignment in assignments.only(
            'school_id',
            'academic_year_id',
            'classroom_id',
            'section_id',
        ):
            enrollment_scope |= Q(
                enrollments__school_id=assignment.school_id,
                enrollments__academic_year_id=assignment.academic_year_id,
                enrollments__classroom_id=assignment.classroom_id,
                enrollments__section_id=assignment.section_id,
                enrollments__is_current=True,
                enrollments__status='active',
            )

        if not enrollment_scope:
            return queryset.none()
        return queryset.filter(enrollment_scope).distinct()

    if user.role == 'parent':
        return queryset.filter(guardians__parent__user=user).distinct()

    if user.role == 'student':
        return queryset.filter(user=user)

    return queryset.none()