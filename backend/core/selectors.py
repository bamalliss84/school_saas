from django.db.models import Prefetch, Q

from .models import (
    Attendance,
    Student,
    StudentEnrollment,
    StudentGuardian,
    Teacher,
    TeacherAssignment,
)


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

def get_teacher_assignments_for_user(user):
    queryset = TeacherAssignment.objects.select_related(
        'teacher', 'school', 'academic_year', 'classroom', 'section', 'subject',
    )
    if not user or not user.is_authenticated:
        return queryset.none()
    if user.role == 'super_admin':
        return queryset
    if not user.school_id:
        return queryset.none()
    queryset = queryset.filter(school_id=user.school_id)
    if user.role == 'school_admin':
        return queryset
    if user.role != 'teacher':
        return queryset.none()
    return queryset.filter(teacher__user=user)


def user_can_manage_teacher_assignment(user, assignment):
    if not user or not user.is_authenticated:
        return False
    if user.role == 'super_admin':
        return True
    if not user.school_id or assignment.school_id != user.school_id:
        return False
    if user.role == 'school_admin':
        return True
    return user.role == 'teacher' and assignment.teacher.user_id == user.id


def get_accessible_student_enrollments_for_user(user):
    queryset = StudentEnrollment.objects.select_related(
        'student', 'school', 'academic_year', 'classroom', 'section',
    )
    student_ids = students_for_user(user).values('pk')
    return queryset.filter(student_id__in=student_ids)


def get_attendance_queryset_for_user(user):
    queryset = Attendance.objects.select_related(
        'student_enrollment', 'student_enrollment__student',
        'student_enrollment__school', 'student_enrollment__academic_year',
        'student_enrollment__classroom', 'student_enrollment__section',
        'teacher_assignment', 'teacher_assignment__teacher', 'academic_term',
    )
    if not user or not user.is_authenticated:
        return queryset.none()
    if user.role == 'super_admin':
        return queryset
    if not user.school_id:
        return queryset.none()
    queryset = queryset.filter(student_enrollment__school_id=user.school_id)
    if user.role == 'school_admin':
        return queryset
    if user.role == 'teacher':
        return queryset.filter(
            teacher_assignment__teacher__user=user,
            teacher_assignment__school_id=user.school_id,
        )
    if user.role == 'parent':
        return queryset.filter(
            student_enrollment__student__guardians__parent__user=user,
        ).distinct()
    if user.role == 'student':
        return queryset.filter(student_enrollment__student__user=user)
    return queryset.none()
