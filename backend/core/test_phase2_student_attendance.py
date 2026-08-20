from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .management.commands.seed_demo_school import DEMO_PASSWORD
from .models import Attendance, SchoolMembership


@override_settings(DEBUG=True)
class Phase2StudentAttendanceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command('seed_demo_school', stdout=StringIO())

    def setUp(self):
        self.client = APIClient()

    def login_and_select(self, username, school_code):
        login = self.client.post('/api/v1/auth/login/', {
            'username': username, 'password': DEMO_PASSWORD,
        }, format='json')
        self.assertEqual(login.status_code, 200, login.data)
        membership = SchoolMembership.objects.get(
            user__username=username, school__code=school_code, role='student',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.data['access']}",
            HTTP_X_SCHOOL_MEMBERSHIP_ID=str(membership.pk),
        )
        return membership

    def test_student_own_attendance_contract_and_statuses(self):
        self.login_and_select('demo_student_a_01', 'DEMO_NOOR')
        response = self.client.get('/api/v1/students/me/attendance/')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['student']['full_name'], 'DEMO Student A 01')
        self.assertEqual(response.data['academic_year']['name'], 'DEMO 2025/2026')
        self.assertGreaterEqual(response.data['total_records'], 15)
        self.assertGreater(response.data['present_count'], 0)
        self.assertGreater(response.data['absent_count'], 0)
        self.assertGreater(response.data['late_count'], 0)
        self.assertGreater(response.data['excused_count'], 0)
        self.assertTrue(all(
            row['student']['id'] == response.data['student']['id']
            for row in response.data['records']
        ))
        self.assertTrue(any(term['term_type'] == 'term_3' for term in response.data['terms']))

    def test_student_own_attendance_filters_without_widening_scope(self):
        self.login_and_select('demo_student_a_01', 'DEMO_NOOR')
        response = self.client.get('/api/v1/students/me/attendance/', {
            'date_from': '2026-08-10', 'date_to': '2026-08-12',
        })
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['total_records'], 3)
        self.assertEqual(
            {row['attendance_date'] for row in response.data['records']},
            {'2026-08-10', '2026-08-11', '2026-08-12'},
        )

    def test_student_own_attendance_is_read_only(self):
        self.login_and_select('demo_student_a_01', 'DEMO_NOOR')
        self.assertEqual(
            self.client.post('/api/v1/students/me/attendance/', {}, format='json').status_code,
            405,
        )

    def test_non_student_cannot_use_student_own_attendance(self):
        login = self.client.post('/api/v1/auth/login/', {
            'username': 'demo_teacher_a', 'password': DEMO_PASSWORD,
        }, format='json')
        membership = SchoolMembership.objects.get(
            user__username='demo_teacher_a', school__code='DEMO_NOOR', role='teacher',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.data['access']}",
            HTTP_X_SCHOOL_MEMBERSHIP_ID=str(membership.pk),
        )
        self.assertEqual(self.client.get('/api/v1/students/me/attendance/').status_code, 403)


    def test_demo_attendance_seed_is_idempotent(self):
        before = Attendance.objects.filter(
            student_enrollment__student__user__username='demo_student_a_01',
            note__startswith='DEMO attendance V1 |',
        ).count()
        call_command('seed_demo_school', stdout=StringIO())
        after = Attendance.objects.filter(
            student_enrollment__student__user__username='demo_student_a_01',
            note__startswith='DEMO attendance V1 |',
        ).count()
        self.assertEqual(before, 15)
        self.assertEqual(after, before)

    def test_historical_student_attendance_is_scoped_to_historical_membership(self):
        self.login_and_select('demo_student_transferred', 'DEMO_NOOR')
        response = self.client.get('/api/v1/students/me/attendance/')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['academic_year']['name'], 'DEMO 2024/2025')
        expected_ids = set(Attendance.objects.filter(
            student_enrollment__student__user__username='demo_student_transferred',
            student_enrollment__school__code='DEMO_NOOR',
            student_enrollment__academic_year__name='DEMO 2024/2025',
        ).values_list('pk', flat=True))
        self.assertEqual({row['id'] for row in response.data['records']}, expected_ids)
