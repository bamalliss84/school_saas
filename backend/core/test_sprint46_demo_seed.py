from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from .models import (
    Attendance, School, SchoolMembership, Student, StudentEnrollment, Teacher, User,
)


@override_settings(DEBUG=True)
class Sprint46DemoSeedTests(TestCase):
    def run_seed(self, *args):
        output = StringIO()
        call_command('seed_demo_school', *args, stdout=output)
        return output.getvalue()

    def snapshot(self):
        return {
            'schools': School.objects.filter(code__startswith='DEMO_').count(),
            'users': User.objects.filter(username__startswith='demo_').count(),
            'students': Student.objects.filter(user__username__startswith='demo_').count(),
            'memberships': SchoolMembership.objects.filter(user__username__startswith='demo_').count(),
            'attendance': Attendance.objects.filter(note='DEMO attendance').count(),
        }

    def test_seed_is_idempotent_and_has_expected_scale(self):
        self.run_seed()
        first = self.snapshot()
        self.run_seed()
        self.assertEqual(self.snapshot(), first)
        self.assertEqual(first['schools'], 2)
        self.assertEqual(first['students'], 21)
        self.assertGreaterEqual(first['attendance'], 20)

    def test_reset_removes_only_demo_data_and_rebuilds_same_shape(self):
        real_school = School.objects.create(name='Real School', code='REAL_KEEP')
        self.run_seed()
        first = self.snapshot()
        self.run_seed('--reset-demo')
        self.assertEqual(self.snapshot(), first)
        self.assertTrue(School.objects.filter(pk=real_school.pk).exists())

    def test_transferred_student_has_historical_and_current_contexts(self):
        self.run_seed()
        user = User.objects.get(username='demo_student_transferred')
        memberships = {
            item.school.code: item.status for item in user.school_memberships.all()
        }
        self.assertEqual(memberships, {'DEMO_NOOR': 'historical', 'DEMO_FUTURE': 'active'})
        enrollments = StudentEnrollment.objects.filter(student__user=user).order_by('academic_year__start_date')
        self.assertEqual(enrollments.count(), 2)
        self.assertFalse(enrollments[0].is_current)
        self.assertTrue(enrollments[1].is_current)
        self.assertNotEqual(enrollments[0].school_id, enrollments[1].school_id)

    @override_settings(DEBUG=False)
    def test_non_debug_guard_requires_explicit_acknowledgement(self):
        with self.assertRaises(CommandError):
            self.run_seed()
        self.assertFalse(School.objects.filter(code__startswith='DEMO_').exists())


class TeacherEmployeeCodeRegressionTests(TestCase):
    def test_second_generated_teacher_code_increments(self):
        from datetime import date
        from .models import AcademicYear

        school = School.objects.create(name='Code School', code='CODE')
        year = AcademicYear.objects.create(
            school=school, name='2025', start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        first = Teacher.objects.create(school=school, academic_year=year, full_name='First')
        second = Teacher.objects.create(school=school, academic_year=year, full_name='Second')
        self.assertEqual(first.employee_code, 'CODE-T00001')
        self.assertEqual(second.employee_code, 'CODE-T00002')
