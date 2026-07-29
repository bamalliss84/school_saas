from django.db.models import Prefetch

from .models import Exam, ExamResult, ExamResultLog, ExamType


def exam_types_for_user(user):
    queryset = ExamType.objects.select_related('school')
    if not user or not user.is_authenticated:
        return queryset.none()
    if user.role == 'super_admin':
        return queryset
    if not user.school_id:
        return queryset.none()
    return queryset.filter(school_id=user.school_id)


def exams_for_user(user):
    results = ExamResult.objects.select_related(
        'student_enrollment__student', 'graded_by', 'approved_by',
    )
    queryset = Exam.objects.select_related(
        'school', 'academic_year', 'academic_term', 'exam_type',
        'teacher_assignment__teacher', 'teacher_assignment__classroom',
        'teacher_assignment__section', 'teacher_assignment__subject', 'created_by',
    ).prefetch_related(Prefetch('results', queryset=results))
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
        return queryset.filter(teacher_assignment__teacher__user=user)
    if user.role == 'parent':
        return queryset.filter(
            results__workflow_status='approved',
            results__student_enrollment__student__guardians__parent__user=user,
        ).distinct()
    if user.role == 'student':
        return queryset.filter(
            results__workflow_status='approved',
            results__student_enrollment__student__user=user,
        ).distinct()
    return queryset.none()


def exam_results_for_user(user):
    queryset = ExamResult.objects.select_related(
        'exam__school', 'exam__academic_year', 'exam__academic_term',
        'exam__exam_type', 'exam__teacher_assignment__teacher',
        'exam__teacher_assignment__classroom',
        'exam__teacher_assignment__section',
        'exam__teacher_assignment__subject',
        'student_enrollment__student', 'student_enrollment__classroom',
        'student_enrollment__section', 'graded_by', 'approved_by',
    )
    if not user or not user.is_authenticated:
        return queryset.none()
    if user.role == 'super_admin':
        return queryset
    if not user.school_id:
        return queryset.none()
    queryset = queryset.filter(exam__school_id=user.school_id)
    if user.role == 'school_admin':
        return queryset
    if user.role == 'teacher':
        return queryset.filter(exam__teacher_assignment__teacher__user=user)
    if user.role == 'parent':
        return queryset.filter(
            workflow_status='approved',
            student_enrollment__student__guardians__parent__user=user,
        ).distinct()
    if user.role == 'student':
        return queryset.filter(
            workflow_status='approved',
            student_enrollment__student__user=user,
        )
    return queryset.none()


def exam_result_logs_for_user(user):
    result_ids = exam_results_for_user(user).values('pk')
    if user.role in ('parent', 'student'):
        return ExamResultLog.objects.none()
    return ExamResultLog.objects.filter(exam_result_id__in=result_ids).select_related(
        'exam_result', 'changed_by',
    )