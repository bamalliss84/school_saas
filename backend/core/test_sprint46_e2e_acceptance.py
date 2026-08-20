from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .management.commands.seed_demo_school import DEMO_PASSWORD
from .models import (
    Announcement, Attendance, Homework, Notification, School, SchoolMembership, Student,
    TeacherAssignment, User,
)


@override_settings(DEBUG=True)
class Sprint46E2EAcceptanceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command('seed_demo_school', stdout=StringIO())

    def setUp(self):
        self.client = APIClient()

    def login(self, username):
        response = self.client.post(
            '/api/v1/auth/login/',
            {'username': username, 'password': DEMO_PASSWORD},
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return response.data

    def membership(self, username, school_code, role=None):
        queryset = SchoolMembership.objects.filter(
            user__username=username, school__code=school_code,
        )
        if role:
            queryset = queryset.filter(role=role)
        return queryset.get()

    def select(self, membership):
        self.client.credentials(
            HTTP_AUTHORIZATION=self.client._credentials['HTTP_AUTHORIZATION'],
            HTTP_X_SCHOOL_MEMBERSHIP_ID=str(membership.pk),
        )

    def result_ids(self, response):
        self.assertEqual(response.status_code, 200, response.data)
        return {row['id'] for row in response.data.get('results', response.data)}

    def test_auth_login_wrong_password_refresh_logout_blacklist(self):
        wrong = self.client.post(
            '/api/v1/auth/login/', {'username': 'demo_teacher_a', 'password': 'wrong'}, format='json',
        )
        self.assertEqual(wrong.status_code, 401)
        tokens = self.login('demo_teacher_a')
        refreshed = self.client.post('/api/v1/auth/refresh/', {'refresh': tokens['refresh']}, format='json')
        self.assertEqual(refreshed.status_code, 200)
        logout = self.client.post('/api/v1/auth/logout/', {'refresh': tokens['refresh']}, format='json')
        self.assertEqual(logout.status_code, 205)
        rejected = self.client.post('/api/v1/auth/refresh/', {'refresh': tokens['refresh']}, format='json')
        self.assertEqual(rejected.status_code, 401)

    def test_multi_school_teacher_context_switch_changes_all_scopes(self):
        self.login('demo_teacher_multi')
        contexts = self.client.get('/api/v1/auth/contexts/')
        self.assertEqual(contexts.status_code, 200)
        self.assertEqual(len(contexts.data['contexts']), 2)
        self.assertEqual(self.client.get('/api/v1/auth/me/').status_code, 409)

        membership_a = self.membership('demo_teacher_multi', 'DEMO_NOOR', 'teacher')
        membership_b = self.membership('demo_teacher_multi', 'DEMO_FUTURE', 'teacher')
        expected_a = set(TeacherAssignment.objects.filter(
            teacher__user__username='demo_teacher_multi', school__code='DEMO_NOOR',
        ).values_list('pk', flat=True))
        expected_b = set(TeacherAssignment.objects.filter(
            teacher__user__username='demo_teacher_multi', school__code='DEMO_FUTURE',
        ).values_list('pk', flat=True))
        self.select(membership_a)
        ids_a = self.result_ids(self.client.get('/api/v1/teachers/me/assignments/'))
        self.select(membership_b)
        ids_b = self.result_ids(self.client.get('/api/v1/teachers/me/assignments/'))
        self.assertEqual(ids_a, expected_a)
        self.assertEqual(ids_b, expected_b)
        self.assertTrue(ids_a.isdisjoint(ids_b))

    def test_teacher_and_admin_cross_school_idor_matrix(self):
        self.login('demo_teacher_a')
        membership_a = self.membership('demo_teacher_a', 'DEMO_NOOR')
        self.select(membership_a)
        foreign_student = Student.objects.filter(school__code='DEMO_FUTURE').first()
        foreign_attendance = Attendance.objects.filter(
            student_enrollment__school__code='DEMO_FUTURE',
        ).first()
        foreign_homework = Homework.objects.filter(school__code='DEMO_FUTURE').first()
        foreign_announcement = Announcement.objects.filter(school__code='DEMO_FUTURE').first()
        self.assertEqual(self.client.get(f'/api/v1/students/{foreign_student.pk}/').status_code, 404)
        self.assertEqual(self.client.get(f'/api/v1/attendance/{foreign_attendance.pk}/').status_code, 404)
        if foreign_homework:
            self.assertEqual(self.client.get(f'/api/v1/homework/{foreign_homework.pk}/').status_code, 404)
        if foreign_announcement:
            self.assertEqual(self.client.get(f'/api/v1/announcements/{foreign_announcement.pk}/').status_code, 404)

        self.client = APIClient()
        self.login('demo_school_a_admin')
        admin_a = self.membership('demo_school_a_admin', 'DEMO_NOOR')
        self.select(admin_a)
        foreign_assignment = TeacherAssignment.objects.filter(school__code='DEMO_FUTURE').first()
        response = self.client.post('/api/v1/exams/', {
            'academic_year': foreign_assignment.academic_year_id,
            'academic_term': foreign_assignment.academic_year.terms.first().pk,
            'teacher_assignment': foreign_assignment.pk,
            'exam_type': foreign_assignment.school.exam_types.first().pk,
            'title': 'DEMO IDOR', 'exam_date': '2025-10-20', 'total_marks': '10',
        }, format='json')
        self.assertIn(response.status_code, (400, 404))

    def test_parent_sees_only_linked_children_and_published_results(self):
        self.login('demo_parent_a')
        membership = self.membership('demo_parent_a', 'DEMO_NOOR')
        self.select(membership)
        children = self.client.get('/api/v1/parents/me/children/')
        self.assertEqual(children.status_code, 200, children.data)
        child_ids = {row['student']['id'] for row in children.data['results']}
        self.assertEqual(len(child_ids), 2)
        unrelated = Student.objects.filter(school__code='DEMO_NOOR').exclude(pk__in=child_ids).first()
        self.assertEqual(self.client.get(f'/api/v1/students/{unrelated.pk}/').status_code, 404)
        results = self.client.get('/api/v1/parents/me/results/')
        self.assertEqual(results.status_code, 200)
        self.assertTrue(results.data['results'])
        self.assertTrue(all(row['is_published'] for row in results.data['results']))

    def test_student_reads_own_academic_resources_and_membership_notifications(self):
        self.login('demo_student_a_01')
        membership = self.membership('demo_student_a_01', 'DEMO_NOOR')
        self.select(membership)
        self.assertEqual(self.client.get('/api/v1/students/me/profile/').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/students/me/results/').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/students/me/attendance/').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/students/me/homework/').status_code, 200)
        announcements = self.client.get('/api/v1/announcements/', {'unread': 'true'})
        self.assertGreaterEqual(announcements.data['count'], 1)
        announcement_id = announcements.data['results'][0]['id']
        self.assertEqual(self.client.post(f'/api/v1/announcements/{announcement_id}/read/').status_code, 200)

    def test_historical_transferred_student_reads_old_data_but_cannot_write(self):
        self.login('demo_student_transferred')
        historical = self.membership('demo_student_transferred', 'DEMO_NOOR', 'student')
        self.select(historical)
        self.assertEqual(self.client.get('/api/v1/auth/context/').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/students/me/academic-history/').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/students/me/results/').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/students/me/attendance/').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/students/me/homework/').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/announcements/').status_code, 200)
        self.assertEqual(self.client.post('/api/v1/attendance/', {}, format='json').status_code, 403)
        self.assertEqual(self.client.post('/api/v1/conversations/start/', {}, format='json').status_code, 403)
        self.assertEqual(self.client.patch('/api/v1/attendance/999/', {}, format='json').status_code, 403)

    def test_notification_membership_isolation_and_read_actions(self):
        self.login('demo_student_transferred')
        current = self.membership('demo_student_transferred', 'DEMO_FUTURE', 'student')
        historical = self.membership('demo_student_transferred', 'DEMO_NOOR', 'student')
        self.select(current)
        current_ids = self.result_ids(self.client.get('/api/v1/notifications/'))
        expected_current = set(Notification.objects.filter(
            recipient_membership=current,
        ).values_list('pk', flat=True))
        self.assertEqual(current_ids, expected_current)
        self.select(historical)
        historical_ids = self.result_ids(self.client.get('/api/v1/notifications/'))
        self.assertTrue(current_ids.isdisjoint(historical_ids))
        if historical_ids:
            notification_id = next(iter(historical_ids))
            self.assertEqual(self.client.post(f'/api/v1/notifications/{notification_id}/read/').status_code, 200)
        self.assertEqual(self.client.post('/api/v1/notifications/read-all/').status_code, 200)

    def test_representative_api_error_contracts(self):
        self.assertEqual(self.client.get('/api/v1/students/').status_code, 401)
        self.login('demo_teacher_a')
        membership = self.membership('demo_teacher_a', 'DEMO_NOOR')
        self.select(membership)
        self.assertEqual(self.client.post('/health/live/', {}, format='json').status_code, 405)
        unsupported = self.client.post(
            '/api/v1/attendance/', data='plain', content_type='text/plain',
        )
        self.assertEqual(unsupported.status_code, 415)
        invalid = self.client.get('/api/v1/announcements/', {'unread': 'maybe'})
        self.assertEqual(invalid.status_code, 400)
