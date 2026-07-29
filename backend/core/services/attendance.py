from django.db import IntegrityError, transaction

from core.models import Attendance


ATTENDANCE_UNIQUE_CONSTRAINT = 'unique_student_attendance_per_day'


def _is_attendance_duplicate_conflict(exc):
    cause = getattr(exc, '__cause__', None)
    diagnostics = getattr(cause, 'diag', None)
    return (
        diagnostics is not None
        and diagnostics.constraint_name == ATTENDANCE_UNIQUE_CONSTRAINT
    )


def _locked_get_or_create(*, enrollment, attendance_date, defaults):
    try:
        # The inner savepoint keeps the outer bulk transaction usable if a
        # concurrent request wins the unique-key race.
        with transaction.atomic():
            return Attendance.objects.select_for_update().get_or_create(
                student_enrollment=enrollment,
                attendance_date=attendance_date,
                defaults=defaults,
            )
    except IntegrityError as exc:
        if not _is_attendance_duplicate_conflict(exc):
            raise
        return (
            Attendance.objects.select_for_update().get(
                student_enrollment=enrollment,
                attendance_date=attendance_date,
            ),
            False,
        )


@transaction.atomic
def save_bulk_attendance(*, teacher_assignment, academic_term, attendance_date, students):
    """Atomically create or update one daily record per enrollment."""
    created_count = 0
    updated_count = 0
    records = []

    for item in students:
        enrollment = item['student_enrollment']
        defaults = {
            'teacher_assignment': teacher_assignment,
            'academic_term': academic_term,
            'status': item['status'],
            'note': item.get('note', ''),
        }
        attendance, created = _locked_get_or_create(
            enrollment=enrollment,
            attendance_date=attendance_date,
            defaults=defaults,
        )
        if created:
            created_count += 1
        else:
            for field, value in defaults.items():
                setattr(attendance, field, value)
            attendance.save()
            updated_count += 1
        records.append(attendance)

    return {
        'created': created_count,
        'updated': updated_count,
        'total': len(records),
        'records': records,
    }