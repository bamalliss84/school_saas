from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from . import test_sprint3_exams
from .context import ensure_legacy_membership
from .models import Homework, HomeworkSubmission, Notification
from .services.homework import close_homework, create_submission_draft, final_submit_homework, grade_submission, publish_homework, return_submission
from .services.homework_completion import completion_flags, completion_status


class Sprint4BHomeworkCompletionTests(APITestCase):
    password = test_sprint3_exams.SprintThreeExamPlatformTests.password
    setUpTestData = classmethod(test_sprint3_exams.SprintThreeExamPlatformTests.setUpTestData.__func__)

    def setUp(self):
        for user in (self.teacher_user, self.student_user, self.parent_user, self.admin_user): ensure_legacy_membership(user)

    def homework(self, *, due_days=5, status='published'):
        now=timezone.now()
        historical = status == 'published' and due_days < 0
        item=Homework.objects.create(school=self.school,academic_year=self.year,academic_term=self.term,teacher_assignment=self.assignment,title='Completion',description='Details',due_date=now+timedelta(days=due_days),max_grade=Decimal('20'),created_by=self.teacher_user,status='published' if historical else 'draft',published_at=now+timedelta(days=due_days-1) if historical else None)
        return item if historical or status != 'published' else publish_homework(homework=item,actor=self.teacher_user)

    def submission(self, homework, status='draft'):
        return HomeworkSubmission.objects.create(homework=homework,student_enrollment=self.enrollment,status=status,submitted_at=timezone.now() if status in ('submitted','graded') else None,grade=Decimal('18') if status=='graded' else None,graded_at=timezone.now() if status=='graded' else None)

    def auth(self,user):
        membership=ensure_legacy_membership(user); self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(user).access_token}',HTTP_X_SCHOOL_MEMBERSHIP_ID=str(membership.pk))

    def test_not_started(self): self.assertEqual(completion_status(self.homework()),'not_started')
    def test_draft(self):
        hw=self.homework(); self.assertEqual(completion_status(hw,self.submission(hw)),'draft')
    def test_submitted(self):
        hw=self.homework(); self.assertEqual(completion_status(hw,self.submission(hw,'submitted')),'submitted')
    def test_graded_has_highest_priority(self):
        hw=self.homework(due_days=-1); self.assertEqual(completion_status(hw,self.submission(hw,'graded')),'graded')
    def test_returned(self):
        hw=self.homework(); self.assertEqual(completion_status(hw,self.submission(hw,'returned')),'returned')
    def test_overdue_without_submission(self): self.assertEqual(completion_status(self.homework(due_days=-1)),'overdue')
    def test_overdue_draft(self):
        hw=self.homework(due_days=-1); self.assertEqual(completion_status(hw,self.submission(hw)),'overdue')
    def test_closed_without_submission(self):
        hw=close_homework(homework=self.homework(),actor=self.teacher_user); self.assertEqual(completion_status(hw),'closed_without_submission')
    def test_closed_with_graded_stays_graded(self):
        hw=self.homework(); sub=self.submission(hw,'graded'); hw=close_homework(homework=hw,actor=self.teacher_user); self.assertEqual(completion_status(hw,sub),'graded')
    def test_flags_allow_new_draft(self): self.assertTrue(completion_flags(self.homework(),None)['can_create_draft'])
    def test_flags_block_historical_write(self): self.assertFalse(completion_flags(self.homework(),None,writable=False)['can_create_draft'])
    def test_flags_allow_returned_edit(self):
        hw=self.homework(); self.assertTrue(completion_flags(hw,self.submission(hw,'returned'))['can_edit'])
    def test_student_homework_dto_contains_completion(self):
        self.homework(); self.auth(self.student_user); row=self.client.get('/api/v1/students/me/homework/').data['results'][0]; self.assertEqual(row['completion_status'],'not_started'); self.assertIn('can_final_submit',row)
    def test_teacher_dashboard(self):
        self.homework(); self.auth(self.teacher_user); response=self.client.get('/api/v1/homework/dashboard/'); self.assertEqual(response.status_code,200); self.assertEqual(response.data['active_homework_count'],1)
    def test_student_dashboard(self):
        self.homework(); self.auth(self.student_user); response=self.client.get('/api/v1/homework/dashboard/'); self.assertEqual(response.status_code,200); self.assertIn('due_this_week_count',response.data)
    def test_parent_dashboard(self):
        self.homework(); self.auth(self.parent_user); response=self.client.get('/api/v1/homework/dashboard/'); self.assertEqual(response.status_code,200); self.assertIn('children_summary',response.data)
    def test_admin_dashboard(self):
        self.homework(); self.auth(self.admin_user); response=self.client.get('/api/v1/homework/dashboard/'); self.assertEqual(response.status_code,200); self.assertIn('overall_completion_rate',response.data)
    def test_publish_creates_notifications_after_commit(self):
        item=Homework.objects.create(school=self.school,academic_year=self.year,academic_term=self.term,teacher_assignment=self.assignment,title='Notify',due_date=timezone.now()+timedelta(days=5),created_by=self.teacher_user)
        with self.captureOnCommitCallbacks(execute=True): publish_homework(homework=item,actor=self.teacher_user)
        self.assertTrue(Notification.objects.filter(notification_type='homework_published').exists())
    def test_grade_creates_notification(self):
        hw=self.homework(); sub=self.submission(hw,'submitted')
        with self.captureOnCommitCallbacks(execute=True): grade_submission(submission=sub,actor=self.teacher_user,grade=Decimal('15'))
        self.assertTrue(Notification.objects.filter(notification_type='homework_graded').exists())
    def test_return_creates_notification(self):
        hw=self.homework(); sub=self.submission(hw,'submitted')
        with self.captureOnCommitCallbacks(execute=True): return_submission(submission=sub,actor=self.teacher_user)
        self.assertTrue(Notification.objects.filter(notification_type='homework_returned').exists())