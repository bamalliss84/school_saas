from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied

from .models import (
    SchoolPeriod, StudentEnrollment, StudentGuardian, TeacherAssignment,
    TimetableEntry,
)


def timetable_weekday(value):
    return (value.weekday() + 1) % 7


def active_entries_on(queryset, date):
    return queryset.filter(
        is_active=True,
    ).filter(
        Q(valid_from__isnull=True) | Q(valid_from__lte=date),
        Q(valid_to__isnull=True) | Q(valid_to__gte=date),
    )


def timetable_entries_base(membership, academic_year):
    return TimetableEntry.objects.filter(
        school_id=membership.school_id, academic_year=academic_year,
    ).select_related(
        'period', 'teacher_assignment__teacher', 'teacher_assignment__classroom',
        'teacher_assignment__section', 'teacher_assignment__subject',
    )


def _student_enrollment(membership, academic_year, student_id=None):
    queryset = StudentEnrollment.objects.filter(
        school_id=membership.school_id, academic_year=academic_year,
    ).select_related('student', 'classroom', 'section')
    if membership.role == 'student':
        queryset = queryset.filter(student__user_id=membership.user_id)
    elif membership.role == 'parent':
        if not student_id or not StudentGuardian.objects.filter(
            parent__user_id=membership.user_id, student_id=student_id,
        ).exists():
            raise NotFound('Student was not found.')
        queryset = queryset.filter(student_id=student_id)
    else:
        raise PermissionDenied('A student or parent context is required.')
    enrollment = queryset.order_by('-is_current', '-pk').first()
    if enrollment is None:
        raise NotFound('Student enrollment was not found.')
    return enrollment


def schedule_scope(request, *, student_id=None, teacher_id=None, classroom_id=None, section_id=None):
    membership = request.active_membership
    year = request.active_academic_year
    if membership is None or year is None:
        raise NotFound('Academic timetable context was not found.')
    queryset = timetable_entries_base(membership, year)
    role = request.active_role
    if role == 'teacher':
        queryset = queryset.filter(teacher_assignment__teacher__user_id=membership.user_id)
    elif role in ('student', 'parent'):
        enrollment = _student_enrollment(membership, year, student_id=student_id)
        queryset = queryset.filter(
            teacher_assignment__classroom_id=enrollment.classroom_id,
            teacher_assignment__section_id=enrollment.section_id,
        )
    elif role in ('school_admin', 'super_admin'):
        if teacher_id:
            queryset = queryset.filter(teacher_assignment__teacher_id=teacher_id)
        if classroom_id:
            queryset = queryset.filter(teacher_assignment__classroom_id=classroom_id)
        if section_id:
            queryset = queryset.filter(teacher_assignment__section_id=section_id)
    else:
        raise PermissionDenied('This role cannot read timetables.')
    return queryset


def periods_for_context(request):
    if request.active_academic_year is None:
        return SchoolPeriod.objects.none()
    return SchoolPeriod.objects.filter(
        school=request.active_school, academic_year=request.active_academic_year,
    ).order_by('sequence', 'start_time', 'pk')


def today_entries(request, *, date=None, **scope):
    date = date or timezone.localdate()
    queryset = schedule_scope(request, **scope).filter(weekday=timetable_weekday(date))
    return active_entries_on(queryset, date), date


def next_entry(request, *, now=None, days=14, **scope):
    now = now or timezone.localtime()
    for offset in range(days + 1):
        date = now.date() + timedelta(days=offset)
        entries = active_entries_on(
            schedule_scope(request, **scope).filter(weekday=timetable_weekday(date)), date,
        ).order_by('period__start_time', 'period__sequence', 'pk')
        for entry in entries:
            if offset or entry.period.start_time > now.time().replace(tzinfo=None):
                return entry, date
    return None, None
