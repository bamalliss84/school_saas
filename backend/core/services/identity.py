from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from core.models import (
    HomeworkActionLog, SchoolMembership, Student, StudentEnrollment,
)
from core.services.exam_results import request_audit_metadata


def sync_legacy_user_context(user, membership=None, enrollment=None):
    """Persist only canonical legacy pointers, never request-local adapter values."""
    if enrollment is not None:
        school_id = enrollment.school_id
        academic_year_id = enrollment.academic_year_id
    elif membership is not None:
        school_id = membership.school_id
        academic_year_id = None
    else:
        return
    type(user).objects.filter(pk=user.pk).update(
        school_id=school_id, academic_year_id=academic_year_id,
    )
    user.school_id = school_id
    user.academic_year_id = academic_year_id


@transaction.atomic
def sync_student_memberships(student):
    locked = Student.objects.select_for_update().get(pk=student.pk)
    enrollments = list(StudentEnrollment.objects.select_for_update().filter(
        student=locked,
    ).select_related('school', 'academic_year'))
    current = next((item for item in enrollments if item.is_current and item.status == 'active'), None)
    if sum(item.is_current and item.status == 'active' for item in enrollments) > 1:
        raise ValidationError('A student can have only one current active enrollment.')
    if not locked.user_id:
        if current:
            Student.objects.filter(pk=locked.pk).update(school_id=current.school_id)
        return current

    memberships = {
        item.school_id: item for item in SchoolMembership.objects.select_for_update().filter(
            user_id=locked.user_id, role='student',
        )
    }
    school_ids = {item.school_id for item in enrollments}
    if current:
        SchoolMembership.objects.filter(
            user_id=locked.user_id, role='student', status='active',
        ).exclude(school_id=current.school_id).update(status='historical', is_default=False)
        for school_id, item in memberships.items():
            if school_id != current.school_id and item.status == 'active':
                item.status = 'historical'
                item.is_default = False
    for school_id in school_ids:
        desired = 'active' if current and school_id == current.school_id else 'historical'
        membership = memberships.get(school_id)
        if membership is None:
            membership = SchoolMembership.objects.create(
                user_id=locked.user_id, school_id=school_id, role='student',
                status=desired, is_default=False,
            )
            memberships[school_id] = membership
        elif membership.status != desired:
            SchoolMembership.objects.filter(pk=membership.pk).update(
                status=desired, is_default=False,
                end_date=None if desired == 'active' else membership.end_date,
            )
    if current:
        SchoolMembership.objects.filter(user_id=locked.user_id).update(is_default=False)
        current_membership = memberships[current.school_id]
        SchoolMembership.objects.filter(pk=current_membership.pk).update(
            status='active', is_default=True, end_date=None,
        )
        Student.objects.filter(pk=locked.pk).update(school_id=current.school_id)
        locked.school_id = current.school_id
        sync_legacy_user_context(locked.user, enrollment=current)
    return current


@transaction.atomic
def set_current_student_enrollment(enrollment):
    locked = StudentEnrollment.objects.select_for_update().select_related('student').get(pk=enrollment.pk)
    StudentEnrollment.objects.filter(student_id=locked.student_id, is_current=True).exclude(
        pk=locked.pk,
    ).update(is_current=False)
    locked.status = 'active'
    locked.is_current = True
    locked.end_date = None
    locked.save(update_fields=('status', 'is_current', 'end_date'))
    sync_student_memberships(locked.student)
    return locked


def _reject_implicit_school_transfer(student, school, becoming_current):
    if not becoming_current:
        return
    current = StudentEnrollment.objects.filter(
        student=student, is_current=True, status='active',
    ).first()
    if current and current.school_id != school.pk:
        raise ValidationError('A school administrator cannot replace a current enrollment in another school.')


@transaction.atomic
def create_student_enrollment(*, student, school, academic_year, classroom, section,
                              status='active', is_current=False, start_date=None, end_date=None):
    locked_student = Student.objects.select_for_update().get(pk=student.pk)
    _reject_implicit_school_transfer(locked_student, school, is_current)
    enrollment = StudentEnrollment.objects.create(
        student=locked_student, school=school, academic_year=academic_year,
        classroom=classroom, section=section, status=status, is_current=False,
        start_date=start_date, end_date=end_date,
    )
    if is_current:
        enrollment = set_current_student_enrollment(enrollment)
    else:
        sync_student_memberships(locked_student)
    sync_parent_memberships(student=locked_student)
    return enrollment


@transaction.atomic
def update_student_enrollment(*, enrollment, school, **changes):
    locked = StudentEnrollment.objects.select_for_update().select_related('student').get(
        pk=enrollment.pk,
    )
    becoming_current = changes.pop('is_current', locked.is_current)
    _reject_implicit_school_transfer(locked.student, school, becoming_current)
    for field, value in changes.items():
        setattr(locked, field, value)
    locked.is_current = False
    locked.save()
    if becoming_current:
        locked = set_current_student_enrollment(locked)
    else:
        sync_student_memberships(locked.student)
    sync_parent_memberships(student=locked.student)
    return locked


@transaction.atomic
def sync_parent_memberships(parent=None, student=None):
    parents = []
    if parent is not None:
        parents = [parent]
    elif student is not None:
        parents = [link.parent for link in student.guardians.select_related('parent__user')]
    for item in parents:
        if not item.user_id:
            continue
        enrollments = StudentEnrollment.objects.filter(
            student__guardians__parent=item,
        ).values('school_id', 'is_current', 'status')
        schools = {}
        for row in enrollments:
            active = row['is_current'] and row['status'] == 'active'
            schools[row['school_id']] = schools.get(row['school_id'], False) or active
        existing = {
            membership.school_id: membership
            for membership in SchoolMembership.objects.select_for_update().filter(
                user_id=item.user_id, role='parent',
            )
        }
        for school_id, active in schools.items():
            desired = 'active' if active else 'historical'
            membership = existing.get(school_id)
            if membership is None:
                SchoolMembership.objects.create(
                    user_id=item.user_id, school_id=school_id, role='parent', status=desired,
                )
            elif membership.status != desired:
                SchoolMembership.objects.filter(pk=membership.pk).update(
                    status=desired, is_default=False if desired == 'historical' else membership.is_default,
                )
    return parents


@transaction.atomic
def sync_teacher_memberships(teacher):
    if not teacher.user_id:
        return []
    assignments = teacher.assignments.values('school_id', 'is_current')
    schools = {}
    for row in assignments:
        schools[row['school_id']] = schools.get(row['school_id'], False) or row['is_current']
    saved = []
    for school_id, has_current in schools.items():
        membership = SchoolMembership.objects.filter(
            user_id=teacher.user_id, school_id=school_id, role='teacher',
        ).first()
        if membership is None:
            membership = SchoolMembership.objects.create(
                user_id=teacher.user_id, school_id=school_id, role='teacher',
                status='active' if has_current else 'historical',
            )
        elif has_current and membership.status == 'historical':
            SchoolMembership.objects.filter(pk=membership.pk).update(status='active', end_date=None)
            membership.status = 'active'
        # Explicit active memberships are intentionally never downgraded here.
        saved.append(membership)
    return saved


def _validate_transfer_destination(current, school, year, classroom, section, transfer_date):
    if not school.is_active:
        raise ValidationError('Destination school is not active.')
    if not year.is_active:
        raise ValidationError('Destination academic year is not active.')
    if hasattr(classroom, 'is_active') and not classroom.is_active:
        raise ValidationError('Destination classroom is not active.')
    if hasattr(section, 'is_active') and not section.is_active:
        raise ValidationError('Destination section is not active.')
    if school.pk == current.school_id:
        raise ValidationError('Destination school must differ from the current school.')
    if (
        year.school_id != school.pk or classroom.school_id != school.pk
        or classroom.academic_year_id != year.pk or section.school_id != school.pk
        or section.academic_year_id != year.pk or section.classroom_id != classroom.pk
    ):
        raise ValidationError('Invalid destination relationships.')
    if current.start_date and transfer_date < current.start_date:
        raise ValidationError('Transfer date cannot precede the current enrollment.')
    if year.start_date and transfer_date < year.start_date or year.end_date and transfer_date > year.end_date:
        raise ValidationError('Transfer date must fall within the destination academic year.')


@transaction.atomic
def transfer_student(*, student, destination_school, destination_academic_year,
                     destination_classroom, destination_section, transfer_date,
                     actor, reason, request=None):
    if not (actor.is_superuser or getattr(actor, 'role', None) == 'super_admin'):
        raise PermissionDenied('Only a super administrator can transfer students between schools.')
    locked_student = Student.objects.select_for_update().get(pk=student.pk)
    current = StudentEnrollment.objects.select_for_update().filter(
        student=locked_student, is_current=True,
    ).select_related('school').first()
    if current is None:
        raise ValidationError('Student has no current enrollment to transfer.')
    _validate_transfer_destination(
        current, destination_school, destination_academic_year,
        destination_classroom, destination_section, transfer_date,
    )
    destination = StudentEnrollment.objects.select_for_update().filter(
        student=locked_student, academic_year=destination_academic_year,
    ).first()
    if destination and (destination.is_current or destination.status == 'active'):
        raise ValidationError('Destination enrollment cannot be reused safely.')

    StudentEnrollment.objects.filter(pk=current.pk).update(
        status='transferred', is_current=False, end_date=transfer_date,
    )
    if destination:
        destination.school = destination_school
        destination.classroom = destination_classroom
        destination.section = destination_section
        destination.status = 'active'
        destination.is_current = True
        destination.start_date = transfer_date
        destination.end_date = None
        destination.save()
    else:
        destination = StudentEnrollment.objects.create(
            student=locked_student, school=destination_school,
            academic_year=destination_academic_year, classroom=destination_classroom,
            section=destination_section, status='active', is_current=True,
            start_date=transfer_date,
        )
    sync_student_memberships(locked_student)
    sync_parent_memberships(student=locked_student)

    HomeworkActionLog.objects.create(
        school=destination_school, actor=actor, action='student_transfer',
        entity_type='student', entity_id=locked_student.pk,
        old_data={'school_id': current.school_id, 'enrollment_id': current.pk},
        new_data={'school_id': destination_school.pk, 'enrollment_id': destination.pk},
        reason=reason, **request_audit_metadata(request),
    )
    return destination
