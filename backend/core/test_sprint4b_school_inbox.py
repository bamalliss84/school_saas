from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from . import test_sprint3_exams
from .context import ensure_legacy_membership
from .models import Conversation, ConversationParticipant, HomeworkActionLog, Message, Notification, SchoolMembership
from .services.messaging import broadcast_notification, send_message, start_conversation, set_conversation_status


class Sprint4BSchoolInboxTests(APITestCase):
    password=test_sprint3_exams.SprintThreeExamPlatformTests.password
    setUpTestData=classmethod(test_sprint3_exams.SprintThreeExamPlatformTests.setUpTestData.__func__)
    def setUp(self):
        self.teacher_m=ensure_legacy_membership(self.teacher_user); self.student_m=ensure_legacy_membership(self.student_user); self.parent_m=ensure_legacy_membership(self.parent_user); self.admin_m=ensure_legacy_membership(self.admin_user)
    def auth(self,user,membership): self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(user).access_token}',HTTP_X_SCHOOL_MEMBERSHIP_ID=str(membership.pk))
    def support(self,membership=None,subject='Help'):
        return start_conversation(creator_membership=membership or self.student_m,participant_membership_ids=(),conversation_type='school_support',subject=subject,category='academic_inquiry')[0]
    def create_api(self,user=None,membership=None,**changes):
        self.auth(user or self.student_user,membership or self.student_m); data={'subject':'Need help','category':'academic_inquiry','message':'Please help'}; data.update(changes); return self.client.post('/api/v1/school-inbox/',data,format='json')
    def test_student_creates_support(self): self.assertEqual(self.create_api().status_code,201)
    def test_parent_creates_support(self): self.assertEqual(self.create_api(self.parent_user,self.parent_m).status_code,201)
    def test_teacher_creates_support(self): self.assertEqual(self.create_api(self.teacher_user,self.teacher_m).status_code,201)
    def test_school_admin_cannot_create_support(self): self.assertEqual(self.create_api(self.admin_user,self.admin_m).status_code,403)
    def test_support_requests_do_not_reuse(self): self.assertNotEqual(self.support(subject='One').pk,self.support(subject='Two').pk)
    def test_student_sees_only_own_support(self):
        own=self.support(); self.support(self.parent_m); self.auth(self.student_user,self.student_m); response=self.client.get('/api/v1/school-inbox/'); self.assertEqual([x['id'] for x in response.data['results']],[own.pk])
    def test_parent_does_not_see_student_support(self):
        self.support(); self.auth(self.parent_user,self.parent_m); self.assertEqual(self.client.get('/api/v1/school-inbox/').data['count'],0)
    def test_admin_sees_school_support(self):
        self.support(); self.support(self.parent_m); self.auth(self.admin_user,self.admin_m); self.assertEqual(self.client.get('/api/v1/school-inbox/').data['count'],2)
    def test_admin_does_not_see_private_conversation(self):
        start_conversation(creator_membership=self.teacher_m,participant_membership_ids=(self.student_m.pk,),conversation_type='teacher_student',subject='Private'); self.auth(self.admin_user,self.admin_m); self.assertEqual(self.client.get('/api/v1/conversations/').data['count'],0)
    def test_support_detail_idor(self):
        item=self.support(); self.auth(self.parent_user,self.parent_m); self.assertEqual(self.client.get(f'/api/v1/school-inbox/{item.pk}/').status_code,404)
    def test_admin_assigns_self(self):
        item=self.support(); self.auth(self.admin_user,self.admin_m); response=self.client.post(f'/api/v1/school-inbox/{item.pk}/assign/',{},format='json'); self.assertEqual(response.status_code,200); self.assertEqual(response.data['status'],'in_progress')
    def test_non_admin_cannot_assign(self):
        item=self.support(); self.auth(self.student_user,self.student_m); self.assertEqual(self.client.post(f'/api/v1/school-inbox/{item.pk}/assign/',{}).status_code,403)
    def test_foreign_assignee_rejected(self):
        foreign=SchoolMembership.objects.create(user=self.other_teacher_user,school=self.other_school,role='school_admin',status='active'); item=self.support(); self.auth(self.admin_user,self.admin_m); self.assertEqual(self.client.post(f'/api/v1/school-inbox/{item.pk}/assign/',{'membership_id':foreign.pk},format='json').status_code,400)
    def test_admin_marks_resolved(self):
        item=self.support(); self.auth(self.admin_user,self.admin_m); response=self.client.post(f'/api/v1/school-inbox/{item.pk}/status/',{'status':'resolved','resolution_note':'Done'},format='json'); self.assertEqual(response.data['status'],'resolved')
    def test_student_cannot_mark_in_progress(self):
        item=self.support(); self.auth(self.student_user,self.student_m); self.assertEqual(self.client.post(f'/api/v1/school-inbox/{item.pk}/status/',{'status':'in_progress'},format='json').status_code,403)
    def test_creator_can_close_support(self):
        item=self.support(); self.auth(self.student_user,self.student_m); self.assertEqual(self.client.post(f'/api/v1/school-inbox/{item.pk}/status/',{'status':'closed'},format='json').status_code,200)
    def test_admin_reply(self):
        item=self.support(); self.auth(self.admin_user,self.admin_m); response=self.client.post(f'/api/v1/school-inbox/{item.pk}/reply/',{'body':'Answer'},format='json'); self.assertEqual(response.status_code,201)
    def test_admin_reply_adds_participant(self):
        item=self.support(); self.auth(self.admin_user,self.admin_m); self.client.post(f'/api/v1/school-inbox/{item.pk}/reply/',{'body':'Answer'},format='json'); self.assertTrue(ConversationParticipant.objects.filter(conversation=item,membership=self.admin_m).exists())
    def test_admin_reply_notifies_creator(self):
        item=self.support(); self.auth(self.admin_user,self.admin_m)
        with self.captureOnCommitCallbacks(execute=True): self.client.post(f'/api/v1/school-inbox/{item.pk}/reply/',{'body':'Answer'},format='json')
        self.assertTrue(Notification.objects.filter(recipient_membership=self.student_m,notification_type='school_reply').exists())
    def test_resolved_support_rejects_reply(self):
        item = set_conversation_status(conversation=self.support(), membership=self.admin_m, status='resolved'); self.auth(self.student_user,self.student_m); self.assertEqual(self.client.post(f'/api/v1/school-inbox/{item.pk}/reply/',{'body':'Again'},format='json').status_code,400)
    def test_historical_support_post_forbidden(self):
        self.student_m.is_default=False; self.student_m.status='historical'; self.student_m.save(); self.auth(self.student_user,self.student_m); self.assertEqual(self.client.post('/api/v1/school-inbox/',{'subject':'x','category':'other'}).status_code,403)
    def test_unauthenticated_inbox_401(self): self.assertEqual(self.client.get('/api/v1/school-inbox/').status_code,401)
    def test_broadcast_students(self):
        self.auth(self.teacher_user,self.teacher_m)
        with self.captureOnCommitCallbacks(execute=True): response=self.client.post('/api/v1/notifications/broadcast/',{'teacher_assignment_id':self.assignment.pk,'audience':'students','title':'Class','body':'Reminder'},format='json')
        self.assertEqual(response.status_code,200); self.assertTrue(Notification.objects.filter(recipient_membership=self.student_m).exists())
    def test_broadcast_parents(self):
        with self.captureOnCommitCallbacks(execute=True): result=broadcast_notification(actor_membership=self.teacher_m,teacher_assignment=self.assignment,student_ids=(),audience='parents',title='Class',body='Reminder')
        self.assertEqual(result['recipient_count'],1); self.assertTrue(Notification.objects.filter(recipient_membership=self.parent_m).exists())
    def test_broadcast_students_and_parents(self):
        with self.captureOnCommitCallbacks(execute=True): result=broadcast_notification(actor_membership=self.teacher_m,teacher_assignment=self.assignment,student_ids=(),audience='students_and_parents',title='Class',body='Reminder')
        self.assertEqual(result['recipient_count'],2)
    def test_broadcast_rejects_outside_student(self):
        self.auth(self.teacher_user,self.teacher_m); self.assertEqual(self.client.post('/api/v1/notifications/broadcast/',{'teacher_assignment_id':self.assignment.pk,'student_ids':[self.other_student.pk],'audience':'students','title':'x','body':'x'},format='json').status_code,400)
    def test_parent_cannot_broadcast(self):
        self.auth(self.parent_user,self.parent_m); self.assertEqual(self.client.post('/api/v1/notifications/broadcast/',{'teacher_assignment_id':self.assignment.pk,'audience':'students','title':'x','body':'x'},format='json').status_code,403)
    def test_broadcast_is_deduplicated_on_callback_retry(self):
        with self.captureOnCommitCallbacks(execute=True): result=broadcast_notification(actor_membership=self.teacher_m,teacher_assignment=self.assignment,student_ids=(),audience='students',title='Class',body='Reminder')
        from .services.messaging import _broadcast_callback
        _broadcast_callback(membership_ids=(self.student_m.pk,),title='Class',body='Reminder',event_id=result['event_id'],action={}); self.assertEqual(Notification.objects.filter(source_type='teacher_broadcast').count(),1)
    def test_broadcast_audit_has_no_body(self):
        with self.captureOnCommitCallbacks(execute=False): broadcast_notification(actor_membership=self.teacher_m,teacher_assignment=self.assignment,student_ids=(),audience='students',title='Class',body='Sensitive content')
        log=HomeworkActionLog.objects.get(action='teacher_broadcast_sent'); self.assertNotIn('Sensitive',str(log.new_data))
    def test_badges_include_notifications(self):
        from .services.notifications import create_notification
        create_notification(recipient_membership=self.student_m,notification_type='system',title='x'); self.auth(self.student_user,self.student_m); response=self.client.get('/api/v1/communication/badges/'); self.assertEqual(response.data['notification_unread'],1)
    def test_badges_include_unread_conversation(self):
        conv=self.support(); send_message(conversation=conv,sender_membership=self.student_m,body='Own'); self.auth(self.student_user,self.student_m); response=self.client.get('/api/v1/communication/badges/'); self.assertEqual(response.data['conversation_unread'],0)
    def test_admin_badges_include_open_inbox(self):
        self.support(); self.auth(self.admin_user,self.admin_m); response=self.client.get('/api/v1/communication/badges/'); self.assertEqual(response.data['school_inbox_open_count'],1)
    def test_contexts_return_conversation_count(self):
        conv=self.support(); self.auth(self.admin_user,self.admin_m); self.client.post(f'/api/v1/school-inbox/{conv.pk}/reply/',{'body':'Reply'},format='json'); self.auth(self.student_user,self.student_m); response=self.client.get('/api/v1/auth/contexts/'); self.assertIn('unread_conversations_count',response.data['contexts'][0])
    def test_school_support_category_required(self): self.assertEqual(self.create_api(category='').status_code,400)
    def test_school_support_invalid_priority(self): self.assertEqual(self.create_api(priority='urgent').status_code,400)
    @override_settings(REST_FRAMEWORK={})
    def test_private_content_not_exposed_in_notification_body(self):
        item=self.support();
        with self.captureOnCommitCallbacks(execute=True): send_message(conversation=item,sender_membership=self.student_m,body='A'*500)
        self.assertTrue(all(len(n.body)<=120 for n in Notification.objects.all()))