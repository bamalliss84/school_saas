from django.db.models import Prefetch

from .models import Exam, ExamResult, ExamResultLog, ExamType


def exam_types_for_user(user, request=None):
    queryset = ExamType.objects.select_related('school')
    if not user or not user.is_authenticated:
        return queryset.none()
    role = getattr(request, 'active_role', None) or getattr(user, 'role', None)
    school = getattr(request, 'active_school', None) or getattr(user, 'school', None)
    if role == 'super_admin':
        return queryset
    if not school:
        return queryset.none()
    return queryset.filter(school=school)


def exams_for_user(user, request=None):
    results = ExamResult.objects.select_related(
        'student_enrollment__student', 'graded_by', 'approved_by', 'published_by',
    )
    queryset = Exam.objects.select_related(
        'school', 'academic_year', 'academic_term', 'exam_type',
        'teacher_assignment__teacher', 'teacher_assignment__classroom',
        'teacher_assignment__section', 'teacher_assignment__subject', 'created_by',
    ).prefetch_related(Prefetch('results', queryset=results))
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
    if role == 'parent':
        return queryset.filter(
            results__workflow_status='approved',
            results__is_published=True,
            results__student_enrollment__student__guardians__parent__user=user,
        ).distinct()
    if role == 'student':
        return queryset.filter(
            results__workflow_status='approved',
            results__is_published=True,
            results__student_enrollment__student__user=user,
        ).distinct()
    return queryset.none()


def exam_results_for_user(user, request=None):
    queryset = ExamResult.objects.select_related(
        'exam__school', 'exam__academic_year', 'exam__academic_term',
        'exam__exam_type', 'exam__teacher_assignment__teacher',
        'exam__teacher_assignment__classroom',
        'exam__teacher_assignment__section',
        'exam__teacher_assignment__subject',
        'student_enrollment__student', 'student_enrollment__classroom',
        'student_enrollment__section', 'graded_by', 'approved_by', 'published_by',
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
    queryset = queryset.filter(exam__school=school)
    if role == 'school_admin':
        return queryset
    if role == 'teacher':
        qs = queryset.filter(exam__teacher_assignment__teacher__user=user)
        if academic_year:
            qs = qs.filter(exam__academic_year=academic_year)
        return qs
    if role == 'parent':
        return queryset.filter(
            workflow_status='approved',
            is_published=True,
            student_enrollment__student__guardians__parent__user=user,
        ).distinct()
    if role == 'student':
        return queryset.filter(
            workflow_status='approved',
            is_published=True,
            student_enrollment__student__user=user,
        )
    return queryset.none()


def exam_result_logs_for_user(user, request=None):
    result_ids = exam_results_for_user(user, request=request).values('pk')
    role = getattr(request, 'active_role', None) or getattr(user, 'role', None)
    if role in ('parent', 'student'):
        return ExamResultLog.objects.none()
    return ExamResultLog.objects.filter(exam_result_id__in=result_ids).select_related(
        'exam_result', 'changed_by', 'published_by',
    )
