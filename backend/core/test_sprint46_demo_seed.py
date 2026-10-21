from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from .models import (
    Attendance, Exam, ExamResult, Homework, School, SchoolMembership, Student, StudentEnrollment, Teacher, User,
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
            'exams': Exam.objects.filter(school__code__startswith='DEMO_').count(),
            'results': ExamResult.objects.filter(exam__school__code__startswith='DEMO_').count(),
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


    def test_release1_admin_demo_dataset_has_operational_depth(self):
        self.run_seed()
        school = School.objects.get(code='DEMO_NOOR')
        self.assertGreaterEqual(
            Attendance.objects.filter(
                student_enrollment__school=school,
                note__startswith='DEMO Release 1 attendance',
            ).count(),
            18,
        )
        homework = Homework.objects.get(
            school=school, title='DEMO Release 1 - واجب مراجعة الرياضيات',
        )
        self.assertEqual(homework.status, 'published')
        self.assertGreaterEqual(homework.submissions.count(), 4)

    def test_student_a01_homework_submission_modes_demo_dataset(self):
        self.run_seed()
        rows = Homework.objects.filter(
            school__code='DEMO_NOOR',
            title__startswith='DEMO Homework - ',
        )
        self.assertEqual(rows.count(), 4)
        self.assertSetEqual(
            set(rows.values_list('submission_type', flat=True)),
            {'none', 'text', 'attachment', 'text_and_attachment'},
        )
        self.assertTrue(rows.filter(
            title='DEMO Homework - Notebook Only',
            submission_type='none', max_grade__isnull=True,
        ).exists())
        self.assertTrue(rows.filter(
            title='DEMO Homework - Attachment Only',
            submission_type='attachment',
        ).exists())

    def test_student_results_acceptance_dataset_has_published_types_and_hidden_result(self):
        self.run_seed()
        enrollment = StudentEnrollment.objects.get(
            student__user__username='demo_student_a_01',
            academic_year__is_active=True,
        )
        results = ExamResult.objects.filter(student_enrollment=enrollment)
        published = results.filter(workflow_status='approved', is_published=True)
        self.assertEqual(published.count(), 5)
        self.assertSetEqual(
            set(published.values_list('exam__exam_type__code', flat=True)),
            {'DEMO_QUIZ', 'DEMO_MONTHLY', 'DEMO_MID', 'DEMO_TERM', 'DEMO_FINAL'},
        )
        self.assertTrue(
            published.filter(
                exam__title='DEMO Monthly Mathematics', score='18.00',
                exam__total_marks='20.00',
            ).exists()
        )
        self.assertTrue(
            published.filter(
                exam__title='DEMO Midterm Science', score='42.00',
                exam__total_marks='50.00',
                remarks__startswith='فهم جيد',
            ).exists()
        )
        self.assertEqual(
            published.values('exam__academic_term__term_type').distinct().count(), 2,
        )
        self.assertTrue(
            published.filter(
                exam__title='DEMO Final Mathematics',
                exam__academic_term__term_type='term_2',
            ).exists()
        )
        hidden = results.get(exam__title='DEMO Unpublished Mathematics Result')
        self.assertEqual(hidden.workflow_status, 'approved')
        self.assertFalse(hidden.is_published)
        self.assertIsNone(hidden.published_at)
        self.assertIsNone(hidden.published_by)

    def test_transferred_student_has_historical_published_result(self):
        self.run_seed()
        historical = ExamResult.objects.get(
            student_enrollment__student__user__username='demo_student_transferred',
            exam__title='DEMO Historical Mathematics Quiz',
        )
        self.assertEqual(historical.student_enrollment.school.code, 'DEMO_NOOR')
        self.assertFalse(historical.student_enrollment.is_current)
        self.assertEqual(historical.workflow_status, 'approved')
        self.assertTrue(historical.is_published)
        self.assertEqual(historical.score, 14)
        self.assertEqual(historical.exam.total_marks, 20)

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
