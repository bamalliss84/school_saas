from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .context import ensure_legacy_membership

from . import test_sprint3_exams
from .models import Homework, HomeworkSubmission
from .services.homework import create_submission_draft, final_submit_homework, publish_homework


class SprintFourAApiCoverageTests(APITestCase):
    password = test_sprint3_exams.SprintThreeExamPlatformTests.password
    setUpTestData = classmethod(test_sprint3_exams.SprintThreeExamPlatformTests.setUpTestData.__func__)

    def auth(self, user=None):
        self.client.force_authenticate(user=user or self.teacher_user)

    def auth_context(self, user):
        membership = ensure_legacy_membership(user)
        self.client.force_authenticate(user=None)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(user).access_token}',
            HTTP_X_SCHOOL_MEMBERSHIP_ID=str(membership.pk),
        )

    def homework(self, title='API homework', published=False, **changes):
        values = {
            'school': self.school, 'academic_year': self.year,
            'academic_term': self.term, 'teacher_assignment': self.assignment,
            'title': title, 'due_date': timezone.now() + timedelta(days=5),
            'max_grade': Decimal('20'), 'created_by': self.teacher_user,
        }
        values.update(changes)
        item = Homework.objects.create(**values)
        return publish_homework(homework=item, actor=self.teacher_user) if published else item

    def submitted(self, homework=None, enrollment=None):
        item = homework or self.homework(published=True)
        submission = HomeworkSubmission.objects.create(
            homework=item, student_enrollment=enrollment or self.enrollment,
            status='submitted', submitted_at=timezone.now(), answer='Answer',
        )
        return item, submission

    def test_01_publish_api(self):
        homework = self.homework()
        self.auth()
        response = self.client.post(f'/api/v1/homework/{homework.pk}/publish/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'published')

    def test_02_close_api(self):
        homework = self.homework(published=True)
        self.auth()
        response = self.client.post(f'/api/v1/homework/{homework.pk}/close/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'closed')

    def test_03_bulk_publish_api(self):
        first, second = self.homework('One'), self.homework('Two')
        self.auth()
        response = self.client.post('/api/v1/homework/bulk-publish/', {
            'homework_ids': [first.pk, second.pk],
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_04_bulk_close_api(self):
        first, second = self.homework('One', True), self.homework('Two', True)
        self.auth()
        response = self.client.post('/api/v1/homework/bulk-close/', {
            'homework_ids': [first.pk, second.pk],
        }, format='json')
        self.assertEqual(response.status_code, 200)

    def test_05_student_submission_create_api(self):
        homework = self.homework(published=True)
        self.auth(self.student_user)
        response = self.client.post(f'/api/v1/homework/{homework.pk}/submission/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'draft')

    def test_06_submission_patch_api(self):
        homework = self.homework(published=True)
        submission = create_submission_draft(
            homework=homework, student_enrollment=self.enrollment, actor=self.student_user,
        )
        self.auth(self.student_user)
        response = self.client.patch(
            f'/api/v1/homework-submissions/{submission.pk}/', {'answer': 'Changed'}, format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['answer'], 'Changed')

    def test_07_final_submit_api(self):
        homework = self.homework(published=True)
        submission = create_submission_draft(
            homework=homework, student_enrollment=self.enrollment, actor=self.student_user,
        )
        self.auth(self.student_user)
        response = self.client.post(f'/api/v1/homework-submissions/{submission.pk}/final-submit/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'submitted')

    def test_08_return_api(self):
        _, submission = self.submitted()
        self.auth()
        response = self.client.post(
            f'/api/v1/homework-submissions/{submission.pk}/return/',
            {'teacher_note': 'Try again'}, format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'returned')

    def test_09_grade_api(self):
        _, submission = self.submitted()
        self.auth()
        response = self.client.post(
            f'/api/v1/homework-submissions/{submission.pk}/grade/',
            {'grade': '17', 'teacher_note': 'Good'}, format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'graded')

    def test_10_bulk_grade_api(self):
        homework = self.homework(published=True)
        _, first = self.submitted(homework, self.enrollment)
        _, second = self.submitted(homework, self.enrollment_two)
        self.auth()
        response = self.client.post('/api/v1/homework-submissions/bulk-grade/', {
            'items': [
                {'submission_id': first.pk, 'grade': '10'},
                {'submission_id': second.pk, 'grade': '15'},
            ],
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_11_teacher_submission_list(self):
        homework, submission = self.submitted()
        self.auth()
        response = self.client.get(f'/api/v1/homework/{homework.pk}/submissions/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['id'], submission.pk)

    def test_12_submission_filtered_list(self):
        homework, submission = self.submitted()
        self.auth()
        response = self.client.get(f'/api/v1/homework-submissions/?homework_id={homework.pk}&status=submitted')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_13_student_own_homework(self):
        self.homework(published=True)
        self.auth(self.student_user)
        self.assertEqual(self.client.get('/api/v1/students/me/homework/').status_code, 200)

    def test_14_parent_child_homework(self):
        homework = self.homework(published=True)
        self.auth_context(self.parent_user)
        response = self.client.get(f'/api/v1/parents/me/children/{self.student.pk}/homework/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['id'], homework.pk)

    def test_15_teacher_own_homework(self):
        self.homework()
        self.auth()
        self.assertEqual(self.client.get('/api/v1/teachers/me/homework/').status_code, 200)

    def test_16_student_summary(self):
        self.submitted()
        self.auth(self.student_user)
        response = self.client.get(f'/api/v1/homework/student/{self.student.pk}/summary/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['statistics']['total'], 1)

    def test_17_class_summary(self):
        self.submitted()
        self.auth()
        response = self.client.get(f'/api/v1/homework/class/{self.classroom.pk}/summary/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['statistics']['total'], 1)

    def test_18_report_bad_date_range(self):
        self.homework()
        self.auth()
        response = self.client.get(
            f'/api/v1/homework/class/{self.classroom.pk}/summary/?date_from=2026-05-02&date_to=2026-05-01',
        )
        self.assertEqual(response.status_code, 400)

    def test_19_delete_empty_draft(self):
        homework = self.homework()
        self.auth()
        self.assertEqual(self.client.delete(f'/api/v1/homework/{homework.pk}/').status_code, 204)

    def test_20_parent_cannot_publish(self):
        homework = self.homework()
        self.auth_context(self.parent_user)
        self.assertEqual(self.client.post(f'/api/v1/homework/{homework.pk}/publish/').status_code, 403)

    def test_21_bulk_missing_id_is_404(self):
        homework = self.homework()
        self.auth()
        response = self.client.post('/api/v1/homework/bulk-publish/', {
            'homework_ids': [homework.pk, 999999],
        }, format='json')
        self.assertEqual(response.status_code, 404)

    def test_22_parent_hides_ungraded_note(self):
        _, submission = self.submitted()
        submission.teacher_note = 'Internal note'
        submission.save()
        self.auth_context(self.parent_user)
        response = self.client.get(f'/api/v1/homework-submissions/{submission.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['teacher_note'], '')

    def test_23_old_access_rejected_for_disabled_school(self):
        self.school.is_active = False
        self.school.save()
        self.auth()
        self.assertEqual(self.client.get('/api/v1/homework/').status_code, 403)