from decimal import Decimal
from unittest.mock import patch

from django.utils import timezone
from rest_framework.test import APITestCase

from . import test_sprint3_exams
from .context import ensure_legacy_membership
from .models import Homework, HomeworkSubmission, Notification
from .services.exam_results import publish_results
from .services.homework import grade_submission, publish_homework, return_submission


class Sprint4BIntegrationTests(APITestCase):
    password = test_sprint3_exams.SprintThreeExamPlatformTests.password
    setUpTestData = classmethod(test_sprint3_exams.SprintThreeExamPlatformTests.setUpTestData.__func__)

    def setUp(self):
        for user in (self.student_user, self.parent_user, self.teacher_user, self.admin_user): ensure_legacy_membership(user)

    def approve(self):
        self.result.workflow_status='approved'; self.result.approved_by=self.admin_user; self.result.approved_at=timezone.now(); self.result.save()

    def test_result_publish_creates_student_and_parent_notifications(self):
        self.approve()
        with self.captureOnCommitCallbacks(execute=True): publish_results(exam=self.exam,changed_by=self.admin_user)
        self.assertEqual(Notification.objects.filter(notification_type='result_published').count(),2)

    def test_result_retry_deduplicates_same_audit_event(self):
        self.approve()
        with self.captureOnCommitCallbacks(execute=True): publish_results(exam=self.exam,changed_by=self.admin_user)
        from .services.notifications import notify_results_published
        notify_results_published(exam_id=self.exam.pk,result_ids=(self.result.pk,)); self.assertEqual(Notification.objects.filter(notification_type='result_published').count(),2)

    def test_homework_notification_not_before_commit(self):
        item=Homework.objects.create(school=self.school,academic_year=self.year,academic_term=self.term,teacher_assignment=self.assignment,title='Deferred',due_date=timezone.now()+timezone.timedelta(days=2),created_by=self.teacher_user)
        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            publish_homework(homework=item,actor=self.teacher_user); self.assertFalse(Notification.objects.exists())
        self.assertEqual(len(callbacks),1)

    def test_notification_failure_does_not_rollback_homework(self):
        item=Homework.objects.create(school=self.school,academic_year=self.year,academic_term=self.term,teacher_assignment=self.assignment,title='Safe',due_date=timezone.now()+timezone.timedelta(days=2),created_by=self.teacher_user)
        with patch('core.services.homework.homework_published_hook',side_effect=RuntimeError('provider unavailable')):
            with self.captureOnCommitCallbacks(execute=True): saved=publish_homework(homework=item,actor=self.teacher_user)
        saved.refresh_from_db(); self.assertEqual(saved.status,'published')

    def test_grade_and_return_use_distinct_events(self):
        item=Homework.objects.create(school=self.school,academic_year=self.year,academic_term=self.term,teacher_assignment=self.assignment,title='Cycles',due_date=timezone.now()+timezone.timedelta(days=2),max_grade=Decimal('20'),created_by=self.teacher_user)
        item=publish_homework(homework=item,actor=self.teacher_user)
        submission=HomeworkSubmission.objects.create(homework=item,student_enrollment=self.enrollment,status='submitted',submitted_at=timezone.now())
        with self.captureOnCommitCallbacks(execute=True): graded=grade_submission(submission=submission,actor=self.teacher_user,grade=Decimal('10'))
        with self.captureOnCommitCallbacks(execute=True): return_submission(submission=graded,actor=self.teacher_user)
        self.assertEqual(Notification.objects.filter(notification_type__in=('homework_graded','homework_returned')).count(),4)