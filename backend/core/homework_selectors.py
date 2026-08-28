from django.db.models import Prefetch, Q

from .models import (
    Homework, HomeworkActionLog, HomeworkAttachment, HomeworkSubmission,
    HomeworkSubmissionAttachment, StudentEnrollment,
)


def _enrollment_scope(user, membership=None, school=None):
    membership = membership or getattr(user, '_active_membership', None)
    school_id = school.id if school else user.school_id
    queryset = StudentEnrollment.objects.filter(school_id=school_id)
    if not membership or membership.status == 'active':
        queryset = queryset.filter(is_current=True, status='active')
    elif membership.status != 'historical':
        return queryset.none()
    role = membership.role if membership else user.role
    if role == 'student':
        return queryset.filter(student__user=user)
    if role == 'parent':
        return queryset.filter(student__guardians__parent__user=user).distinct()
    return queryset.none()



def homework_for_user(user, request=None):
    queryset = Homework.objects.select_related(
        'school', 'academic_year', 'academic_term', 'created_by',
        'teacher_assignment__teacher', 'teacher_assignment__classroom',
        'teacher_assignment__section', 'teacher_assignment__subject',
    ).prefetch_related(
        Prefetch('attachments', queryset=HomeworkAttachment.objects.select_related('uploaded_by')),
        Prefetch('submissions', queryset=HomeworkSubmission.objects.select_related(
            'student_enrollment__student', 'graded_by',
        ).prefetch_related('attachments')),
    )
    if not user or not user.is_authenticated:
        return queryset.none()

    role = getattr(request, 'active_role', None) or getattr(user, 'role', None)
    school = getattr(request, 'active_school', None) or getattr(user, 'school', None)
    academic_year = getattr(request, 'active_academic_year', None) or getattr(user, 'academic_year', None)

    if role == 'super_admin':
        return queryset
    if not school:
        return queryset.none()
    queryset = queryset.filter(school=school)
    if role == 'school_admin':
        return queryset
    if role == 'teacher':
        qs = queryset.filter(teacher_assignment__teacher__user=user)
        if academic_year:
            qs = qs.filter(academic_year=academic_year)
        return qs
    if role not in ('student', 'parent'):
        return queryset.none()
    membership = getattr(request, 'active_membership', None) if request else getattr(user, '_active_membership', None)
    scope = Q()
    for enrollment in _enrollment_scope(user, membership, school=school).only(
        'academic_year_id', 'classroom_id', 'section_id',
    ):
        scope |= Q(
            academic_year_id=enrollment.academic_year_id,
            teacher_assignment__classroom_id=enrollment.classroom_id,
            teacher_assignment__section_id=enrollment.section_id,
        )
    if not scope:
        return queryset.none()
    return queryset.filter(scope, status__in=('published', 'closed')).distinct()


def submissions_for_user(user, request=None):
    queryset = HomeworkSubmission.objects.select_related(
        'homework__school', 'homework__academic_year', 'homework__academic_term',
        'homework__teacher_assignment__teacher',
        'homework__teacher_assignment__classroom',
        'homework__teacher_assignment__section',
        'homework__teacher_assignment__subject',
        'student_enrollment__student', 'student_enrollment__classroom',
        'student_enrollment__section', 'graded_by',
    ).prefetch_related(Prefetch(
        'attachments',
        queryset=HomeworkSubmissionAttachment.objects.select_related('uploaded_by'),
    ))
    if not user or not user.is_authenticated:
        return queryset.none()

    role = getattr(request, 'active_role', None) or getattr(user, 'role', None)
    school = getattr(request, 'active_school', None) or getattr(user, 'school', None)
    academic_year = getattr(request, 'active_academic_year', None) or getattr(user, 'academic_year', None)

    if role == 'super_admin':
        return queryset
    if not school:
        return queryset.none()
    queryset = queryset.filter(homework__school=school)
    if role == 'school_admin':
        return queryset
    if role == 'teacher':
        qs = queryset.filter(homework__teacher_assignment__teacher__user=user)
        if academic_year:
            qs = qs.filter(homework__academic_year=academic_year)
        return qs
    membership = getattr(request, 'active_membership', None) if request else getattr(user, '_active_membership', None)
    if membership and membership.status == 'historical':
        queryset = queryset.filter(homework__status__in=('published', 'closed'))
    if role == 'student':
        return queryset.filter(
            student_enrollment__student__user=user,
            student_enrollment__school=school,
        )
    if role == 'parent':
        return queryset.filter(
            student_enrollment__student__guardians__parent__user=user,
            student_enrollment__school=school,
        ).distinct()
    return queryset.none()


def homework_logs_for_user(user, request=None):
    queryset = HomeworkActionLog.objects.select_related('school', 'actor')
    role = getattr(request, 'active_role', None) or getattr(user, 'role', None)
    school = getattr(request, 'active_school', None) or getattr(user, 'school', None)
    if not user or not user.is_authenticated or role not in ('super_admin', 'school_admin'):
        return queryset.none()
    if role == 'super_admin':
        return queryset
    if not school:
        return queryset.none()
    return queryset.filter(school=school)