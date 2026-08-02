from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from . import test_sprint3_exams
from .context import ensure_legacy_membership
from .models import Conversation, ConversationParticipant, Message, Notification, SchoolMembership
from .services.messaging import mark_conversation_read, send_message, start_conversation


class Sprint4BMessagingTests(APITestCase):
    password=test_sprint3_exams.SprintThreeExamPlatformTests.password
    setUpTestData=classmethod(test_sprint3_exams.SprintThreeExamPlatformTests.setUpTestData.__func__)
    def setUp(self):
        self.teacher_m=ensure_legacy_membership(self.teacher_user); self.student_m=ensure_legacy_membership(self.student_user); self.parent_m=ensure_legacy_membership(self.parent_user); self.admin_m=ensure_legacy_membership(self.admin_user)
    def auth(self,user,membership): self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(user).access_token}',HTTP_X_SCHOOL_MEMBERSHIP_ID=str(membership.pk))
    def conversation(self): return start_conversation(creator_membership=self.teacher_m,participant_membership_ids=(self.student_m.pk,),conversation_type='teacher_student',subject='Math',related_type='student',related_id=self.student.pk)[0]
    def test_conversation_requires_same_school_participants(self):
        other=SchoolMembership.objects.create(user=self.student_user,school=self.other_school,role='parent',status='active')
        with self.assertRaises(Exception): start_conversation(creator_membership=self.teacher_m,participant_membership_ids=(other.pk,),conversation_type='teacher_student',subject='x')
    def test_participant_model_rejects_cross_school(self):
        conv=self.conversation(); other=SchoolMembership.objects.create(user=self.student_user,school=self.other_school,role='parent',status='active'); item=ConversationParticipant(conversation=conv,membership=other,participant_role='parent')
        with self.assertRaises(DjangoValidationError): item.full_clean()
    def test_conversation_reuse(self):
        first=self.conversation(); second=self.conversation(); self.assertEqual(first.pk,second.pk)
    def test_different_subject_does_not_force_reuse_by_subject_policy(self):
        first=self.conversation(); second,_=start_conversation(creator_membership=self.teacher_m,participant_membership_ids=(self.student_m.pk,),conversation_type='teacher_student',subject='Other',related_type='general')
        self.assertNotEqual(first.pk,second.pk)
    def test_send_message(self): self.assertEqual(send_message(conversation=self.conversation(),sender_membership=self.teacher_m,body='Hello').body,'Hello')
    def test_nonparticipant_cannot_send(self):
        with self.assertRaises(Exception): send_message(conversation=self.conversation(),sender_membership=self.parent_m,body='No')
    def test_empty_message_rejected(self):
        with self.assertRaises(Exception): send_message(conversation=self.conversation(),sender_membership=self.teacher_m,body='  ')
    def test_script_message_rejected(self):
        with self.assertRaises(Exception): send_message(conversation=self.conversation(),sender_membership=self.teacher_m,body='<script>alert(1)</script>')
    def test_reply_target_same_conversation(self):
        first=self.conversation(); other,_=start_conversation(creator_membership=self.teacher_m,participant_membership_ids=(self.parent_m.pk,),conversation_type='teacher_parent',subject='Parent'); target=send_message(conversation=other,sender_membership=self.teacher_m,body='x')
        with self.assertRaises(Exception): send_message(conversation=first,sender_membership=self.teacher_m,body='reply',reply_to=target)
    def test_message_notification_after_commit(self):
        conv=self.conversation()
        with self.captureOnCommitCallbacks(execute=True): message=send_message(conversation=conv,sender_membership=self.teacher_m,body='Hello')
        notice=Notification.objects.get(source_type='message',source_id=message.pk); self.assertEqual(notice.recipient_membership,self.student_m)
    def test_sender_not_notified(self):
        with self.captureOnCommitCallbacks(execute=True): send_message(conversation=self.conversation(),sender_membership=self.teacher_m,body='Hello')
        self.assertFalse(Notification.objects.filter(recipient_membership=self.teacher_m).exists())
    def test_notification_not_before_commit(self):
        with self.captureOnCommitCallbacks(execute=False) as callbacks: send_message(conversation=self.conversation(),sender_membership=self.teacher_m,body='Hello'); self.assertFalse(Notification.objects.exists())
        self.assertEqual(len(callbacks),1)
    def test_mark_read_updates_only_current_participant(self):
        conv=self.conversation(); participant=mark_conversation_read(conversation=conv,membership=self.student_m); self.assertIsNotNone(participant.last_read_at); self.assertIsNone(conv.participants.get(membership=self.teacher_m).last_read_at)
    def test_teacher_starts_assigned_student_api(self):
        self.auth(self.teacher_user,self.teacher_m); response=self.client.post('/api/v1/conversations/start/',{'conversation_type':'teacher_student','subject':'Study','teacher_assignment_id':self.assignment.pk,'student_id':self.student.pk},format='json'); self.assertEqual(response.status_code,201)
    def test_teacher_cannot_start_unrelated_student(self):
        self.auth(self.teacher_user,self.teacher_m); response=self.client.post('/api/v1/conversations/start/',{'conversation_type':'teacher_student','subject':'Study','teacher_assignment_id':self.assignment.pk,'student_id':self.other_student.pk},format='json'); self.assertEqual(response.status_code,400)
    def test_student_starts_current_teacher(self):
        self.auth(self.student_user,self.student_m); response=self.client.post('/api/v1/conversations/start/',{'conversation_type':'teacher_student','subject':'Question','teacher_assignment_id':self.assignment.pk},format='json'); self.assertEqual(response.status_code,201)
    def test_list_only_active_membership(self):
        conv=self.conversation(); self.auth(self.student_user,self.student_m); response=self.client.get('/api/v1/conversations/'); self.assertEqual([row['id'] for row in response.data['results']],[conv.pk])
    def test_detail_idor_is_404(self):
        conv=self.conversation(); self.auth(self.parent_user,self.parent_m); self.assertEqual(self.client.get(f'/api/v1/conversations/{conv.pk}/').status_code,404)
    def test_messages_paginated(self):
        conv=self.conversation(); send_message(conversation=conv,sender_membership=self.teacher_m,body='One'); self.auth(self.student_user,self.student_m); response=self.client.get(f'/api/v1/conversations/{conv.pk}/messages/'); self.assertEqual(response.status_code,200); self.assertIn('results',response.data)
    def test_send_api(self):
        conv=self.conversation(); self.auth(self.student_user,self.student_m); response=self.client.post(f'/api/v1/conversations/{conv.pk}/messages/',{'body':'Reply'},format='json'); self.assertEqual(response.status_code,201)
    def test_historical_get_and_read_allowed(self):
        conv=self.conversation(); self.student_m.is_default=False; self.student_m.status='historical'; self.student_m.save(); self.auth(self.student_user,self.student_m); self.assertEqual(self.client.get(f'/api/v1/conversations/{conv.pk}/').status_code,200); self.assertEqual(self.client.post(f'/api/v1/conversations/{conv.pk}/read/').status_code,200)
    def test_historical_message_blocked(self):
        conv=self.conversation(); self.student_m.is_default=False; self.student_m.status='historical'; self.student_m.save(); self.auth(self.student_user,self.student_m); self.assertEqual(self.client.post(f'/api/v1/conversations/{conv.pk}/messages/',{'body':'No'},format='json').status_code,403)
    def test_close_and_reopen(self):
        conv=self.conversation(); self.auth(self.teacher_user,self.teacher_m); self.assertEqual(self.client.post(f'/api/v1/conversations/{conv.pk}/close/').status_code,200); self.assertEqual(self.client.post(f'/api/v1/conversations/{conv.pk}/reopen/').status_code,200)
    def test_unauthenticated_is_401(self): self.assertEqual(self.client.get('/api/v1/conversations/').status_code,401)