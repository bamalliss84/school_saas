import shutil
import tempfile
from datetime import timedelta
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from . import test_sprint3_exams
from .models import Homework, HomeworkAttachment, HomeworkSubmissionAttachment
from .services.homework import (
    add_homework_attachment, add_submission_attachment,
    create_submission_draft, delete_homework_attachment,
    delete_submission_attachment, publish_homework, validate_attachment,
)


class SprintFourAAttachmentTests(APITestCase):
    password = test_sprint3_exams.SprintThreeExamPlatformTests.password
    setUpTestData = classmethod(
        test_sprint3_exams.SprintThreeExamPlatformTests.setUpTestData.__func__
    )

    def setUp(self):
        self.media_root = tempfile.mkdtemp(prefix='school-saas-tests-')
        self.settings_override = override_settings(MEDIA_ROOT=self.media_root)
        self.settings_override.enable()

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def auth(self, user=None):
        self.client.force_authenticate(user=user or self.teacher_user)

    def homework(self, published=False):
        item = Homework.objects.create(
            school=self.school, academic_year=self.year, academic_term=self.term,
            teacher_assignment=self.assignment, title='Files homework',
            due_date=timezone.now() + timedelta(days=5), created_by=self.teacher_user,
        )
        return publish_homework(homework=item, actor=self.teacher_user) if published else item

    def text_file(self, name='answer.txt', content=b'answer'):
        return SimpleUploadedFile(name, content, content_type='text/plain')

    def test_01_allowed_attachment(self):
        values = validate_attachment(self.text_file(), kind='homework')
        self.assertEqual(values['content_type'], 'text/plain')

    def test_02_blocked_extension(self):
        with self.assertRaises(Exception):
            validate_attachment(
                SimpleUploadedFile('malware.exe', b'MZ', content_type='application/octet-stream'),
                kind='homework',
            )

    def test_03_double_extension_rejected(self):
        with self.assertRaises(Exception):
            validate_attachment(
                SimpleUploadedFile('lesson.pdf.exe', b'MZ', content_type='application/pdf'),
                kind='homework',
            )

    def test_04_mime_mismatch_rejected(self):
        with self.assertRaises(Exception):
            validate_attachment(
                SimpleUploadedFile('lesson.pdf', b'not pdf', content_type='text/plain'),
                kind='homework',
            )

    def test_05_empty_file_rejected(self):
        with self.assertRaises(Exception):
            validate_attachment(self.text_file(content=b''), kind='homework')

    @override_settings(MAX_HOMEWORK_ATTACHMENT_SIZE_MB=0)
    def test_06_oversized_file_rejected(self):
        with self.assertRaises(Exception):
            validate_attachment(self.text_file(), kind='homework')

    @override_settings(MAX_ATTACHMENTS_PER_HOMEWORK=1)
    def test_07_max_count_enforced(self):
        homework = self.homework()
        add_homework_attachment(
            homework=homework, files=[self.text_file('one.txt')], actor=self.teacher_user,
        )
        with self.assertRaises(Exception):
            add_homework_attachment(
                homework=homework, files=[self.text_file('two.txt')], actor=self.teacher_user,
            )

    def test_08_multiple_upload_is_atomic(self):
        homework = self.homework()
        created = add_homework_attachment(
            homework=homework,
            files=[self.text_file('one.txt'), self.text_file('two.txt')],
            actor=self.teacher_user,
        )
        self.assertEqual(len(created), 2)
        self.assertEqual(homework.attachments.count(), 2)

    def test_09_invalid_batch_saves_nothing(self):
        homework = self.homework()
        with self.assertRaises(Exception):
            add_homework_attachment(
                homework=homework,
                files=[self.text_file('good.txt'), self.text_file('bad.exe')],
                actor=self.teacher_user,
            )
        self.assertFalse(homework.attachments.exists())

    def test_10_student_adds_submission_attachment(self):
        homework = self.homework(published=True)
        submission = create_submission_draft(
            homework=homework, student_enrollment=self.enrollment,
            actor=self.student_user,
        )
        created = add_submission_attachment(
            submission=submission, files=[self.text_file()], actor=self.student_user,
        )
        self.assertEqual(len(created), 1)

    def test_11_teacher_cannot_modify_student_attachment(self):
        homework = self.homework(published=True)
        submission = create_submission_draft(
            homework=homework, student_enrollment=self.enrollment,
            actor=self.student_user,
        )
        with self.assertRaises(Exception):
            add_submission_attachment(
                submission=submission, files=[self.text_file()], actor=self.teacher_user,
            )

    def test_12_file_delete_runs_after_commit(self):
        homework = self.homework()
        attachment = add_homework_attachment(
            homework=homework, files=[self.text_file()], actor=self.teacher_user,
        )[0]
        with patch.object(attachment.file.storage, 'delete') as storage_delete:
            with self.captureOnCommitCallbacks(execute=True):
                delete_homework_attachment(
                    attachment=attachment, actor=self.teacher_user,
                )
        storage_delete.assert_called_once()
        self.assertFalse(HomeworkAttachment.objects.filter(pk=attachment.pk).exists())

    def test_13_file_delete_not_run_before_commit(self):
        homework = self.homework()
        attachment = add_homework_attachment(
            homework=homework, files=[self.text_file()], actor=self.teacher_user,
        )[0]
        with patch.object(attachment.file.storage, 'delete') as storage_delete:
            with self.captureOnCommitCallbacks(execute=False) as callbacks:
                delete_homework_attachment(
                    attachment=attachment, actor=self.teacher_user,
                )
                storage_delete.assert_not_called()
        self.assertEqual(len(callbacks), 1)

    def test_14_storage_delete_failure_does_not_restore_database(self):
        homework = self.homework()
        attachment = add_homework_attachment(
            homework=homework, files=[self.text_file()], actor=self.teacher_user,
        )[0]
        with patch.object(
            attachment.file.storage, 'delete', side_effect=OSError('storage unavailable'),
        ):
            with self.captureOnCommitCallbacks(execute=True):
                delete_homework_attachment(
                    attachment=attachment, actor=self.teacher_user,
                )
        self.assertFalse(HomeworkAttachment.objects.filter(pk=attachment.pk).exists())

    def test_15_multipart_api_upload(self):
        homework = self.homework()
        self.auth()
        response = self.client.post(
            f'/api/v1/homework/{homework.pk}/attachments/',
            {'files': [self.text_file()]}, format='multipart',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data), 1)

    def test_16_submission_attachment_idor_is_404(self):
        homework = self.homework(published=True)
        submission = create_submission_draft(
            homework=homework, student_enrollment=self.enrollment,
            actor=self.student_user,
        )
        attachment = add_submission_attachment(
            submission=submission, files=[self.text_file()], actor=self.student_user,
        )[0]
        self.auth(self.other_teacher_user)
        response = self.client.delete(
            f'/api/v1/homework-submissions/{submission.pk}/attachments/{attachment.pk}/',
        )
        self.assertEqual(response.status_code, 404)

    def test_17_admin_deletion_is_audited(self):
        homework = self.homework(published=True)
        submission = create_submission_draft(
            homework=homework, student_enrollment=self.enrollment,
            actor=self.student_user,
        )
        attachment = add_submission_attachment(
            submission=submission, files=[self.text_file()], actor=self.student_user,
        )[0]
        with self.captureOnCommitCallbacks(execute=True):
            delete_submission_attachment(attachment=attachment, actor=self.admin_user)
        self.assertFalse(HomeworkSubmissionAttachment.objects.filter(pk=attachment.pk).exists())