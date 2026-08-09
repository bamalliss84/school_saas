from django.db import transaction
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from core.models import SchoolPeriod, TimetableEntry


def require_timetable_admin(membership):
    if (
        membership is None or not membership.can_write
        or membership.role not in ('school_admin', 'super_admin')
    ):
        raise PermissionDenied('School administrator access is required.')


def _ranges_overlap(left_from, left_to, right_from, right_to):
    return (left_from is None or right_to is None or left_from <= right_to) and (
        right_from is None or left_to is None or right_from <= left_to
    )


def _conflict(code, entry, message):
    return {
        'code': code, 'weekday': entry.weekday, 'period_id': entry.period_id,
        'teacher_assignment_id': entry.teacher_assignment_id, 'message': message,
    }


def validate_entry_conflicts(entry, *, exclude_id=None, pending=None):
    conflicts = []
    if pending is None:
        candidates = TimetableEntry.objects.filter(
            school_id=entry.school_id, academic_year_id=entry.academic_year_id,
            weekday=entry.weekday, period_id=entry.period_id, is_active=True,
        ).exclude(pk=exclude_id)
        items = list(candidates.select_related('teacher_assignment'))
    else:
        items = pending
    for other in items:
        if not other.is_active or (other.pk and other.pk == exclude_id):
            continue
        if other.weekday != entry.weekday or other.period_id != entry.period_id:
            continue
        if not _ranges_overlap(entry.valid_from, entry.valid_to, other.valid_from, other.valid_to):
            continue
        if other.teacher_assignment_id == entry.teacher_assignment_id:
            conflicts.append(_conflict('exact_duplicate', entry, 'This timetable cell already exists.'))
        elif other.teacher_assignment.teacher_id == entry.teacher_assignment.teacher_id:
            conflicts.append(_conflict('teacher_conflict', entry, 'The teacher has another lesson in this period.'))
        elif (
            other.teacher_assignment.classroom_id == entry.teacher_assignment.classroom_id
            and other.teacher_assignment.section_id == entry.teacher_assignment.section_id
        ):
            conflicts.append(_conflict('class_section_conflict', entry, 'The class section has another lesson in this period.'))
    return conflicts


def build_entry(*, membership, academic_year, values, instance=None):
    require_timetable_admin(membership)
    period = SchoolPeriod.objects.filter(
        pk=values['period_id'], school_id=membership.school_id,
        academic_year=academic_year,
    ).first()
    if period is None:
        raise NotFound('Period was not found.')
    from core.models import TeacherAssignment
    assignment = TeacherAssignment.objects.filter(
        pk=values['teacher_assignment_id'], school_id=membership.school_id,
        academic_year=academic_year,
    ).select_related('teacher', 'classroom', 'section', 'subject').first()
    if assignment is None:
        raise NotFound('Teacher assignment was not found.')
    item = instance or TimetableEntry(
        school=membership.school, academic_year=academic_year, created_by=membership.user,
    )
    item.teacher_assignment = assignment
    item.period = period
    for field in ('weekday', 'room_or_location', 'valid_from', 'valid_to', 'is_active'):
        if field in values:
            setattr(item, field, values[field])
    item.full_clean()
    return item


@transaction.atomic
def save_entry(*, membership, academic_year, values, instance=None):
    item = build_entry(
        membership=membership, academic_year=academic_year, values=values, instance=instance,
    )
    conflicts = validate_entry_conflicts(item, exclude_id=item.pk)
    if conflicts:
        raise ValidationError({'conflicts': conflicts})
    item.save()
    return item


@transaction.atomic
def bulk_apply(*, membership, academic_year, cells, validate_only=False):
    require_timetable_admin(membership)
    if not cells:
        raise ValidationError({'cells': 'At least one cell is required.'})
    identifiers = [cell.get('id') for cell in cells if cell.get('id')]
    if len(identifiers) != len(set(identifiers)):
        raise ValidationError({'cells': 'Duplicate entry IDs are not allowed.'})
    scoped = list(TimetableEntry.objects.select_for_update().filter(
        school_id=membership.school_id, academic_year=academic_year,
    ).select_related('teacher_assignment', 'period'))
    existing = {item.pk: item for item in scoped if item.pk in identifiers}
    if len(existing) != len(set(identifiers)):
        raise NotFound('One or more timetable entries were not found.')
    built, clears, errors = [], [], []
    operated_ids = set()
    for index, cell in enumerate(cells):
        action = cell.get('action', 'upsert')
        if action == 'clear':
            if not cell.get('id'):
                errors.append({'index': index, 'code': 'missing_id', 'message': 'Clear requires an entry ID.'})
            else:
                clears.append(existing[cell['id']])
                operated_ids.add(cell['id'])
            continue
        try:
            instance = existing.get(cell.get('id'))
            if instance is not None:
                from copy import copy
                instance = copy(instance)
                operated_ids.add(instance.pk)
            item = build_entry(
                membership=membership, academic_year=academic_year, values=cell,
                instance=instance,
            )
            built.append((index, item))
        except ValidationError as exc:
            errors.append({'index': index, 'code': 'invalid_cell', 'message': str(exc.detail)})
    projected = [item for item in scoped if item.pk not in operated_ids]
    for index, item in built:
        conflicts = validate_entry_conflicts(item, exclude_id=item.pk, pending=projected)
        if conflicts:
            errors.extend({'index': index, **error} for error in conflicts)
        projected.append(item)
    if errors:
        if validate_only:
            return {'valid': False, 'errors': errors, 'valid_cells': len(cells) - len(errors)}
        raise ValidationError({'conflicts': errors})
    if validate_only:
        return {'valid': True, 'errors': [], 'valid_cells': len(cells)}
    for item in clears:
        item.delete()
    for _, item in built:
        item.save()
    return {'created_or_updated': len(built), 'cleared': len(clears), 'entries': [item for _, item in built]}


@transaction.atomic
def replace_periods(*, membership, academic_year, rows):
    require_timetable_admin(membership)
    items = []
    for row in rows:
        item = SchoolPeriod(
            school=membership.school, academic_year=academic_year, **row,
        )
        item.full_clean()
        items.append(item)
    for index, left in enumerate(items):
        for right in items[index + 1:]:
            if left.sequence == right.sequence or (
                left.start_time < right.end_time and left.end_time > right.start_time
            ):
                raise ValidationError({'periods': 'Period sequences and times must not overlap.'})
    if TimetableEntry.objects.filter(
        school=membership.school, academic_year=academic_year,
    ).exists():
        raise ValidationError('Periods cannot be replaced while timetable entries exist.')
    SchoolPeriod.objects.filter(
        school=membership.school, academic_year=academic_year,
    ).delete()
    return SchoolPeriod.objects.bulk_create(items)


@transaction.atomic
def copy_schedule(*, membership, academic_year, source_weekday=None, target_weekday=None,
                  source_classroom_id, source_section_id, target_classroom_id=None,
                  target_section_id=None, clear_target=False, validate_only=False):
    require_timetable_admin(membership)
    source = TimetableEntry.objects.filter(
        school=membership.school, academic_year=academic_year,
        teacher_assignment__classroom_id=source_classroom_id,
        teacher_assignment__section_id=source_section_id, is_active=True,
    ).select_related('teacher_assignment', 'period')
    if source_weekday is not None:
        source = source.filter(weekday=source_weekday)
    target_classroom_id = target_classroom_id or source_classroom_id
    target_section_id = target_section_id or source_section_id
    from core.models import TeacherAssignment
    assignments = TeacherAssignment.objects.filter(
        school=membership.school, academic_year=academic_year,
        classroom_id=target_classroom_id, section_id=target_section_id, is_current=True,
    )
    by_subject = {item.subject_id: item for item in assignments.select_related('teacher')}
    cells = []
    for item in source:
        assignment = by_subject.get(item.teacher_assignment.subject_id)
        if assignment is None:
            raise ValidationError({'assignment': 'Target class lacks a compatible subject assignment.'})
        cells.append({
            'teacher_assignment_id': assignment.pk, 'period_id': item.period_id,
            'weekday': target_weekday if target_weekday is not None else item.weekday,
            'room_or_location': item.room_or_location,
            'valid_from': item.valid_from, 'valid_to': item.valid_to, 'is_active': True,
        })
    if clear_target:
        target = TimetableEntry.objects.filter(
            school=membership.school, academic_year=academic_year,
            teacher_assignment__classroom_id=target_classroom_id,
            teacher_assignment__section_id=target_section_id,
        )
        if target_weekday is not None:
            target = target.filter(weekday=target_weekday)
        cells = [
            {'id': item_id, 'action': 'clear'}
            for item_id in target.values_list('id', flat=True)
        ] + cells
    return bulk_apply(
        membership=membership, academic_year=academic_year,
        cells=cells, validate_only=validate_only,
    )
