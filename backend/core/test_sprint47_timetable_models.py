from datetime import date, time

from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from .models import (
    AcademicYear, Classroom, School, SchoolMembership, SchoolPeriod,
    SchoolTimetableConfig, Section, Subject, Teacher, TeacherAssignment,
    TimetableEntry, User,
)
from .services.timetable import save_entry


class TimetableModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.school = School.objects.create(name='Schedule School', code='TT')
        cls.year = AcademicYear.objects.create(
            school=cls.school, name='2026', start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31), is_active=True,
        )
        cls.user = User.objects.create_user(
            username='tt_admin', password='x', role='school_admin', school=cls.school,
        )
        cls.membership = SchoolMembership.objects.create(
            user=cls.user, school=cls.school, role='school_admin', status='active',
        )
        cls.teacher_user = User.objects.create_user(
            username='tt_teacher', password='x', role='teacher', school=cls.school,
        )
        SchoolMembership.objects.create(
            user=cls.teacher_user, school=cls.school, role='teacher', status='active',
        )
        cls.teacher = Teacher.objects.create(
            user=cls.teacher_user, school=cls.school, academic_year=cls.year,
            full_name='Timetable Teacher', employee_code='TT-T1',
        )
        cls.classroom = Classroom.objects.create(
            school=cls.school, academic_year=cls.year, name='Grade 1', code='G1',
        )
        cls.section = Section.objects.create(
            school=cls.school, academic_year=cls.year, classroom=cls.classroom,
            name='A', code='A',
        )
        cls.subject = Subject.objects.create(school=cls.school, name='Math', code='MATH')
        cls.assignment = TeacherAssignment.objects.create(
            teacher=cls.teacher, school=cls.school, academic_year=cls.year,
            classroom=cls.classroom, section=cls.section, subject=cls.subject,
        )
        cls.config = SchoolTimetableConfig.objects.create(
            school=cls.school, academic_year=cls.year, working_days=[0, 1, 2, 3, 4],
        )
        cls.period = SchoolPeriod.objects.create(
            school=cls.school, academic_year=cls.year, name='First', sequence=1,
            start_time=time(7), end_time=time(7, 45), kind='lesson',
        )

    def values(self, **overrides):
        values = {
            'teacher_assignment_id': self.assignment.pk, 'period_id': self.period.pk,
            'weekday': 0, 'valid_from': date(2026, 1, 1),
            'valid_to': date(2026, 6, 30), 'room_or_location': '', 'is_active': True,
        }
        values.update(overrides)
        return values

    def test_period_rejects_invalid_and_overlapping_times(self):
        with self.assertRaises(DjangoValidationError):
            SchoolPeriod.objects.create(
                school=self.school, academic_year=self.year, name='Bad', sequence=2,
                start_time=time(8), end_time=time(8),
            )
        with self.assertRaises(DjangoValidationError):
            SchoolPeriod.objects.create(
                school=self.school, academic_year=self.year, name='Overlap', sequence=2,
                start_time=time(7, 30), end_time=time(8),
            )

    def test_break_cannot_receive_teaching_entry(self):
        break_period = SchoolPeriod.objects.create(
            school=self.school, academic_year=self.year, name='Break', sequence=2,
            start_time=time(7, 45), end_time=time(8), kind='break',
        )
        with self.assertRaises(DjangoValidationError):
            TimetableEntry.objects.create(
                school=self.school, academic_year=self.year,
                teacher_assignment=self.assignment, period=break_period, weekday=0,
            )

    def test_overlapping_same_assignment_is_blocked_but_versions_are_allowed(self):
        save_entry(membership=self.membership, academic_year=self.year, values=self.values())
        with self.assertRaises(ValidationError):
            save_entry(
                membership=self.membership, academic_year=self.year,
                values=self.values(valid_from=date(2026, 6, 1), valid_to=date(2026, 8, 1)),
            )
        second = save_entry(
            membership=self.membership, academic_year=self.year,
            values=self.values(valid_from=date(2026, 7, 1), valid_to=date(2026, 12, 31)),
        )
        self.assertIsNotNone(second.pk)

    def test_non_working_day_rejected(self):
        with self.assertRaises(DjangoValidationError):
            TimetableEntry.objects.create(
                school=self.school, academic_year=self.year,
                teacher_assignment=self.assignment, period=self.period, weekday=5,
            )
