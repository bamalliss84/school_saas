from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Exam,
    ExamResult,
    ExamResultLog,
    ExamType,
    SchoolMembership,
    StudentEnrollment,
    TeacherAssignment,
)


@override_settings(DEBUG=True)
class M26ExamActiveContextHardeningTests(TestCase):
    """Regression coverage for the canonical membership-scoped exam contract."""

    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo_school', stdout=StringIO())
        cls.teacher_user = SchoolMembership.objects.get(
            user__username='demo_teacher_multi', school__code='DEMO_NOOR', role='teacher',
        ).user
        cls.membership_a = SchoolMembership.objects.get(
            user=cls.teacher_user, school__code='DEMO_NOOR', role='teacher',
        )
        cls.membership_b = SchoolMembership.objects.get(
            user=cls.teacher_user, school__code='DEMO_FUTURE', role='teacher',
        )
        cls.assignment_a = TeacherAssignment.objects.filter(
            teacher__user=cls.teacher_user, school=cls.membership_a.school,
            academic_year__is_active=True,
        ).first()
        cls.assignment_b = TeacherAssignment.objects.filter(
            teacher__user=cls.teacher_user, school=cls.membership_b.school,
            academic_year__is_active=True,
        ).first()
        cls.exam_type_a = ExamType.objects.filter(school=cls.membership_a.school).first()
        cls.exam_type_b = ExamType.objects.filter(school=cls.membership_b.school).first()
        cls.exam_a = Exam.objects.create(
            school=cls.membership_a.school,
            academic_year=cls.assignment_a.academic_year,
            academic_term=cls.assignment_a.academic_year.terms.first(),
            teacher_assignment=cls.assignment_a,
            exam_type=cls.exam_type_a,
            created_by=cls.teacher_user,
            title='M2.6 School A Exam',
            exam_date=cls.assignment_a.academic_year.terms.first().start_date + timedelta(days=2),
            total_marks=Decimal('20'),
        )
        cls.exam_b = Exam.objects.create(
            school=cls.membership_b.school,
            academic_year=cls.assignment_b.academic_year,
            academic_term=cls.assignment_b.academic_year.terms.first(),
            teacher_assignment=cls.assignment_b,
            exam_type=cls.exam_type_b,
            created_by=cls.teacher_user,
            title='M2.6 School B Exam',
            exam_date=cls.assignment_b.academic_year.terms.first().start_date + timedelta(days=2),
            total_marks=Decimal('20'),
        )
        cls.enrollment_a = StudentEnrollment.objects.filter(
            school=cls.membership_a.school,
            academic_year=cls.assignment_a.academic_year,
            classroom=cls.assignment_a.classroom,
            section=cls.assignment_a.section,
        ).first()
        cls.enrollment_b = StudentEnrollment.objects.filter(
            school=cls.membership_b.school,
            academic_year=cls.assignment_b.academic_year,
            classroom=cls.assignment_b.classroom,
            section=cls.assignment_b.section,
        ).first()
        cls.result_a = ExamResult.objects.create(
            exam=cls.exam_a, student_enrollment=cls.enrollment_a,
            score=Decimal('15'), status='present', graded_by=cls.teacher_user,
        )
        cls.result_b = ExamResult.objects.create(
            exam=cls.exam_b, student_enrollment=cls.enrollment_b,
            score=Decimal('16'), status='present',
        )

    def setUp(self):
        self.client = APIClient()

    def auth(self, membership):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(membership.user).access_token}',
            HTTP_X_SCHOOL_MEMBERSHIP_ID=str(membership.pk),
        )

    def test_exam_types_and_exams_follow_active_school_and_year(self):
        self.auth(self.membership_a)
        types = self.client.get('/api/v1/exam-types/')
        exams = self.client.get('/api/v1/exams/')
        self.assertEqual(types.status_code, 200, types.data)
        self.assertTrue(types.data['results'])
        self.assertTrue(all(row['school'] == self.membership_a.school_id for row in types.data['results']))
        self.assertIn(self.exam_a.pk, {row['id'] for row in exams.data['results']})
        self.assertNotIn(self.exam_b.pk, {row['id'] for row in exams.data['results']})

    def test_school_admin_exam_and_result_lists_are_limited_to_active_year(self):
        admin_membership = SchoolMembership.objects.get(
            user__username='demo_school_a_admin', school=self.membership_a.school,
            role='school_admin',
        )
        self.auth(admin_membership)
        active_year = admin_membership.school.academic_years.get(is_active=True)
        exams = self.client.get('/api/v1/exams/')
        results = self.client.get('/api/v1/exam-results/')
        self.assertEqual(exams.status_code, 200, exams.data)
        self.assertEqual(results.status_code, 200, results.data)
        self.assertTrue(exams.data['results'])
        self.assertTrue(all(row['academic_year'] == active_year.pk for row in exams.data['results']))
        active_exam_ids = {row['id'] for row in exams.data['results']}
        self.assertTrue(all(row['exam'] in active_exam_ids for row in results.data['results']))

    def test_same_user_switching_membership_switches_exam_and_result_scope(self):
        self.auth(self.membership_a)
        a_exam_ids = {row['id'] for row in self.client.get('/api/v1/exams/').data['results']}
        a_result_ids = {row['id'] for row in self.client.get('/api/v1/exam-results/').data['results']}
        self.auth(self.membership_b)
        b_exam_ids = {row['id'] for row in self.client.get('/api/v1/exams/').data['results']}
        b_result_ids = {row['id'] for row in self.client.get('/api/v1/exam-results/').data['results']}
        self.assertIn(self.exam_a.pk, a_exam_ids)
        self.assertNotIn(self.exam_a.pk, b_exam_ids)
        self.assertIn(self.exam_b.pk, b_exam_ids)
        self.assertIn(self.result_a.pk, a_result_ids)
        self.assertNotIn(self.result_a.pk, b_result_ids)
        self.assertIn(self.result_b.pk, b_result_ids)

    def test_direct_foreign_exam_result_and_log_ids_are_hidden(self):
        self.auth(self.membership_a)
        ExamResultLog.objects.create(
            exam_result=self.result_b, action='update', changed_by=self.teacher_user,
        )
        self.assertEqual(self.client.get(f'/api/v1/exams/{self.exam_b.pk}/').status_code, 404)
        self.assertEqual(self.client.get(f'/api/v1/exam-results/{self.result_b.pk}/').status_code, 404)
        self.assertEqual(
            self.client.get(f'/api/v1/exam-results/{self.result_b.pk}/logs/').status_code,
            404,
        )

    def test_teacher_can_mutate_own_active_assignment_but_not_other_context(self):
        self.auth(self.membership_a)
        own = self.client.patch(
            f'/api/v1/exam-results/{self.result_a.pk}/', {'score': '17'}, format='json',
        )
        foreign = self.client.patch(
            f'/api/v1/exam-results/{self.result_b.pk}/', {'score': '17'}, format='json',
        )
        self.assertEqual(own.status_code, 200, own.data)
        self.assertEqual(foreign.status_code, 404)

    def test_single_and_bulk_result_mutations_preserve_atomic_validation(self):
        self.auth(self.membership_a)
        single = self.client.patch(
            f'/api/v1/exam-results/{self.result_a.pk}/',
            {'status': 'excused', 'score': None, 'remarks': 'Approved excuse'},
            format='json',
        )
        self.assertEqual(single.status_code, 200, single.data)
        before = ExamResult.objects.get(pk=self.result_a.pk)
        bulk = self.client.post('/api/v1/exam-results/bulk/', {
            'exam': self.exam_a.pk,
            'results': [
                {'student_enrollment': self.enrollment_a.pk, 'score': '18', 'status': 'present'},
                {'student_enrollment': self.enrollment_b.pk, 'score': '18', 'status': 'present'},
            ],
        }, format='json')
        self.assertEqual(bulk.status_code, 400)
        after = ExamResult.objects.get(pk=self.result_a.pk)
        self.assertEqual((after.status, after.score), (before.status, before.score))

    def test_submit_requires_eligible_result_and_teacher_has_no_admin_workflow(self):
        self.auth(self.membership_a)
        ungraded = ExamResult.objects.create(
            exam=self.exam_a,
            student_enrollment=StudentEnrollment.objects.filter(
                school=self.membership_a.school,
                academic_year=self.assignment_a.academic_year,
                classroom=self.assignment_a.classroom,
                section=self.assignment_a.section,
            ).exclude(pk=self.enrollment_a.pk).first(),
            status='not_graded',
        )
        self.assertEqual(
            self.client.post(f'/api/v1/exam-results/{ungraded.pk}/submit/', {}).status_code,
            400,
        )
        submitted = self.client.post(f'/api/v1/exam-results/{self.result_a.pk}/submit/', {})
        self.assertEqual(submitted.status_code, 200, submitted.data)
        self.assertEqual(submitted.data['workflow_status'], 'submitted')
        self.assertEqual(
            self.client.post(f'/api/v1/exam-results/{self.result_a.pk}/approve/', {}).status_code,
            403,
        )

    def test_historical_context_reads_but_rejects_exam_and_result_writes(self):
        self.membership_a.status = 'historical'
        self.membership_a.is_default = False
        self.membership_a.save(update_fields=('status', 'is_default', 'updated_at'))
        self.auth(self.membership_a)
        self.assertEqual(self.client.get('/api/v1/exams/').status_code, 200)
        self.assertEqual(
            self.client.patch(f'/api/v1/exams/{self.exam_a.pk}/', {'notes': 'blocked'}).status_code,
            403,
        )
        self.assertEqual(
            self.client.patch(f'/api/v1/exam-results/{self.result_a.pk}/', {'score': '19'}).status_code,
            403,
        )
