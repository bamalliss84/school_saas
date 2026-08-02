import tempfile
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from . import test_sprint3_exams
from .context import ensure_legacy_membership
from .models import MessageAttachment
from .services.messaging import add_message_attachments, delete_message_attachment, send_message, start_conversation


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class Sprint4BMessageAttachmentTests(APITestCase):
    password=test_sprint3_exams.SprintThreeExamPlatformTests.password
    setUpTestData=classmethod(test_sprint3_exams.SprintThreeExamPlatformTests.setUpTestData.__func__)
    def setUp(self):
        self.teacher_m=ensure_legacy_membership(self.teacher_user); self.student_m=ensure_legacy_membership(self.student_user)
        self.conversation=start_conversation(creator_membership=self.teacher_m,participant_membership_ids=(self.student_m.pk,),conversation_type='teacher_student',subject='Files')[0]
        self.message=send_message(conversation=self.conversation,sender_membership=self.teacher_m,body='File')
    def pdf(self,name='safe.pdf',content=b'%PDF-1.4 safe'): return SimpleUploadedFile(name,content,content_type='application/pdf')
    def auth(self): self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.teacher_user).access_token}',HTTP_X_SCHOOL_MEMBERSHIP_ID=str(self.teacher_m.pk))
    def test_add_safe_pdf(self): self.assertEqual(len(add_message_attachments(message=self.message,membership=self.teacher_m,files=[self.pdf()])),1)
    def test_empty_file_rejected(self):
        with self.assertRaises(Exception): add_message_attachments(message=self.message,membership=self.teacher_m,files=[self.pdf(content=b'')])
    def test_double_extension_rejected(self):
        with self.assertRaises(Exception): add_message_attachments(message=self.message,membership=self.teacher_m,files=[self.pdf('bad.exe.pdf')])
    def test_mime_mismatch_rejected(self):
        file=SimpleUploadedFile('safe.pdf',b'%PDF-1.4',content_type='image/png')
        with self.assertRaises(Exception): add_message_attachments(message=self.message,membership=self.teacher_m,files=[file])
    def test_non_sender_rejected(self):
        with self.assertRaises(Exception): add_message_attachments(message=self.message,membership=self.student_m,files=[self.pdf()])
    @override_settings(MAX_ATTACHMENTS_PER_MESSAGE=1)
    def test_count_limit(self):
        with self.assertRaises(Exception): add_message_attachments(message=self.message,membership=self.teacher_m,files=[self.pdf('a.pdf'),self.pdf('b.pdf')])
    def test_delete_after_commit(self):
        item=add_message_attachments(message=self.message,membership=self.teacher_m,files=[self.pdf()])[0]
        with patch.object(item.file.storage,'delete') as delete:
            with self.captureOnCommitCallbacks(execute=True): delete_message_attachment(attachment=item,membership=self.teacher_m)
        delete.assert_called_once(); self.assertFalse(MessageAttachment.objects.filter(pk=item.pk).exists())
    def test_other_membership_cannot_delete(self):
        item=add_message_attachments(message=self.message,membership=self.teacher_m,files=[self.pdf()])[0]
        with self.assertRaises(Exception): delete_message_attachment(attachment=item,membership=self.student_m)
    def test_attachment_api(self):
        self.auth(); response=self.client.post(f'/api/v1/messages/{self.message.pk}/attachments/',{'files':[self.pdf()]},format='multipart'); self.assertEqual(response.status_code,201); self.assertNotIn('file',response.data[0])