from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib import admin, messages
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.db import IntegrityError, transaction
from django.test import RequestFactory
from django.utils import timezone
from rest_framework.test import APITestCase

from . import test_sprint3_exams
from .admin import HomeworkSubmissionAdmin
from .models import Homework, HomeworkActionLog, HomeworkSubmission
from .services.homework import (
    bulk_grade_submissions, bulk_publish_homework, close_homework,
    create_submission_draft, final_submit_homework, grade_submission,
    publish_homework, return_submission, update_submission_draft,
)


class SprintFourAHomeworkTests(APITestCase):
    password = test_sprint3_exams.SprintThreeExamPlatformTests.password

    @classmethod
    def setUpTestData(cls):
        test_sprint3_exams.SprintThreeExamPlatformTests.setUpTestData.__func__(cls)
        cls.term.end_date = cls.year.end_date
        cls.term.save(update_fields=['end_date'])
        cls.other_term.end_date = cls.other_year.end_date
        cls.other_term.save(update_fields=['end_date'])

    def auth(self, user=None):
        self.client.force_authenticate(user=user or self.teacher_user)

    def make_homework(self, title='Algebra practice', **changes):
        values = {
            'school': self.school, 'academic_year': self.year,
            'academic_term': self.term, 'teacher_assignment': self.assignment,
            'title': title, 'description': 'Solve exercises.',
            'due_date': timezone.now() + timedelta(days=7),
            'max_grade': Decimal('20'), 'created_by': self.teacher_user,
        }
        values.update(changes)
        return Homework.objects.create(**values)

    def publish(self, homework=None):
        return publish_homework(homework=homework or self.make_homework(), actor=self.teacher_user)

    def submission(self, homework=None):
        sub = create_submission_draft(
            homework=homework or self.publish(), student_enrollment=self.enrollment,
            actor=self.student_user,
        )
        sub.answer = 'Sample Answer'
        sub.save(update_fields=('answer',))
        return sub


    def test_01_unauthenticated_is_401(self):
        self.assertEqual(self.client.get('/api/v1/homework/').status_code, 401)

    def test_02_teacher_creates_draft(self):
        self.auth()
        response = self.client.post('/api/v1/homework/', {
            'academic_year': self.year.pk, 'academic_term': self.term.pk,
            'teacher_assignment': self.assignment.pk, 'title': 'New',
            'due_date': (timezone.now() + timedelta(days=4)).isoformat(),
            'max_grade': '10',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'draft')

    def test_03_teacher_updates_draft(self):
        homework = self.make_homework()
        self.auth()
        response = self.client.patch(f'/api/v1/homework/{homework.pk}/', {'title': 'Updated'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'Updated')

    def test_04_publish_and_close(self):
        homework = self.publish()
        self.assertIsNotNone(homework.published_at)
        self.assertEqual(close_homework(homework=homework, actor=self.teacher_user).status, 'closed')

    def test_05_draft_hidden_from_student(self):
        self.make_homework()
        self.auth(self.student_user)
        self.assertEqual(self.client.get('/api/v1/homework/').data['count'], 0)

    def test_06_published_visible_to_student(self):
        homework = self.publish()
        self.auth(self.student_user)
        ids = [row['id'] for row in self.client.get('/api/v1/homework/').data['results']]
        self.assertIn(homework.pk, ids)

    def test_07_published_visible_to_parent(self):
        homework = self.publish()
        self.auth(self.parent_user)
        ids = [row['id'] for row in self.client.get('/api/v1/homework/').data['results']]
        self.assertIn(homework.pk, ids)

    def test_08_other_tenant_is_404(self):
        other = Homework.objects.create(
            school=self.other_school, academic_year=self.other_year,
            academic_term=self.other_term, teacher_assignment=self.other_assignment,
            title='Other', due_date=timezone.now() + timedelta(days=4),
            created_by=self.other_teacher_user,
        )
        self.auth()
        self.assertEqual(self.client.get(f'/api/v1/homework/{other.pk}/').status_code, 404)

    def test_09_invalid_dates_are_400(self):
        self.auth()
        now = timezone.now()
        response = self.client.post('/api/v1/homework/', {
            'academic_year': self.year.pk, 'academic_term': self.term.pk,
            'teacher_assignment': self.assignment.pk, 'title': 'Invalid',
            'publish_at': (now + timedelta(days=3)).isoformat(),
            'due_date': (now + timedelta(days=2)).isoformat(),
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_10_hook_runs_after_commit(self):
        homework = self.make_homework()
        with patch('core.services.homework.homework_published_hook') as hook:
            with self.captureOnCommitCallbacks(execute=True):
                publish_homework(homework=homework, actor=self.teacher_user)
        hook.assert_called_once_with(homework_id=homework.pk)

    def test_11_hook_not_before_commit(self):
        homework = self.make_homework()
        with patch('core.services.homework.homework_published_hook') as hook:
            with self.captureOnCommitCallbacks(execute=False) as callbacks:
                publish_homework(homework=homework, actor=self.teacher_user)
                hook.assert_not_called()
        self.assertEqual(len(callbacks), 1)

    def test_12_bulk_publish_rolls_back(self):
        good = self.make_homework('Good')
        bad = self.make_homework('Expired', due_date=timezone.now() - timedelta(days=1))
        with self.assertRaises(Exception):
            bulk_publish_homework(homework_items=[good, bad], actor=self.teacher_user)
        good.refresh_from_db()
        self.assertEqual(good.status, 'draft')

    def test_13_create_submission_draft(self):
        self.assertEqual(self.submission().status, 'draft')

    def test_14_submission_unique(self):
        homework = self.publish()
        self.assertEqual(self.submission(homework).pk, self.submission(homework).pk)

    def test_15_update_and_final_submit(self):
        submission = update_submission_draft(
            submission=self.submission(), actor=self.student_user, answer='Answer',
        )
        saved = final_submit_homework(submission=submission, actor=self.student_user)
        self.assertEqual(saved.status, 'submitted')
        self.assertIsNotNone(saved.submitted_at)

    def test_16_no_edit_after_submit(self):
        submission = final_submit_homework(submission=self.submission(), actor=self.student_user)
        with self.assertRaises(Exception):
            update_submission_draft(submission=submission, actor=self.student_user, answer='Changed')

    def test_17_return_then_edit(self):
        submitted = final_submit_homework(submission=self.submission(), actor=self.student_user)
        returned = return_submission(submission=submitted, actor=self.teacher_user, teacher_note='Revise')
        saved = update_submission_draft(submission=returned, actor=self.student_user, answer='Revised')
        self.assertEqual(saved.answer, 'Revised')

    def test_18_grade_submission(self):
        submitted = final_submit_homework(submission=self.submission(), actor=self.student_user)
        saved = grade_submission(submission=submitted, actor=self.teacher_user, grade=Decimal('18'))
        self.assertEqual(saved.status, 'graded')
        self.assertEqual(saved.grade, Decimal('18'))

    def test_19_invalid_grade_rejected(self):
        submitted = final_submit_homework(submission=self.submission(), actor=self.student_user)
        with self.assertRaises(Exception):
            grade_submission(submission=submitted, actor=self.teacher_user, grade=Decimal('21'))

    def test_20_bulk_grade_rolls_back(self):
        homework = self.publish()
        first = final_submit_homework(submission=self.submission(homework), actor=self.student_user)
        second = HomeworkSubmission.objects.create(
            homework=homework, student_enrollment=self.enrollment_two,
            status='submitted', submitted_at=timezone.now(),
        )
        with self.assertRaises(Exception):
            bulk_grade_submissions(items=[
                {'submission': first, 'grade': Decimal('10')},
                {'submission': second, 'grade': Decimal('30')},
            ], actor=self.teacher_user)
        first.refresh_from_db()
        self.assertEqual(first.status, 'submitted')

    def test_21_closed_rejects_submission(self):
        homework = close_homework(homework=self.publish(), actor=self.teacher_user)
        with self.assertRaises(Exception):
            create_submission_draft(
                homework=homework, student_enrollment=self.enrollment,
                actor=self.student_user,
            )

    def test_22_summary_counts_students(self):
        homework = self.publish()
        final_submit_homework(submission=self.submission(homework), actor=self.student_user)
        self.auth()
        response = self.client.get(f'/api/v1/homework/{homework.pk}/summary/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['target_students'], 2)
        self.assertEqual(response.data['submitted'], 1)

    def test_23_invalid_filter_is_400(self):
        self.auth()
        self.assertEqual(self.client.get('/api/v1/homework/?status=bad').status_code, 400)

    def test_24_database_rejects_negative_grade(self):
        submission = self.submission()
        with self.assertRaises(IntegrityError), transaction.atomic():
            HomeworkSubmission.objects.filter(pk=submission.pk).update(grade=-1)

    def test_25_audit_never_stores_answer(self):
        submission = self.submission()
        update_submission_draft(submission=submission, actor=self.student_user, answer='Secret answer')
        log = HomeworkActionLog.objects.filter(action='update').latest('id')
        self.assertNotIn('Secret answer', str(log.new_data))
    def test_26_admin_bulk_grade_uses_service(self):
        submitted = final_submit_homework(
            submission=self.submission(), actor=self.student_user,
        )
        model_admin = HomeworkSubmissionAdmin(HomeworkSubmission, admin.site)
        request = RequestFactory().post(
            '/admin/core/homeworksubmission/',
            {'grade': '16', 'teacher_note': 'Admin graded'},
        )
        request.user = self.admin_user
        request.session = {}
        request._messages = FallbackStorage(request)
        model_admin.grade_selected(
            request, HomeworkSubmission.objects.filter(pk=submitted.pk),
        )
        submitted.refresh_from_db()
        self.assertEqual(submitted.status, 'graded')
        self.assertEqual(list(get_messages(request))[-1].level, messages.SUCCESS)