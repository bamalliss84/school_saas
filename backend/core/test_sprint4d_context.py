from django.test import TestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import SchoolMembership
from .test_sprint4d_memberships import Sprint4DFixtureMixin


class MembershipContextAPITests(Sprint4DFixtureMixin, TestCase):
    def test_single_membership_auto_selects_without_header(self):
        self.membership_b.delete(); self.auth()
        self.assertEqual(self.client.get('/api/v1/auth/me/').status_code, 200)

    def test_multiple_active_memberships_require_context(self):
        self.auth(); response = self.client.get('/api/v1/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['errors']['code'], 'context_required')

    def test_owned_header_selects_context(self):
        self.auth(membership=self.membership_b); response = self.client.get('/api/v1/auth/context/')
        self.assertEqual(response.data['membership_id'], self.membership_b.pk)

    def test_foreign_membership_header_is_not_found(self):
        other = SchoolMembership.objects.create(user=self.student_user, school=self.school_b, role='parent')
        self.auth(membership=other)
        self.assertEqual(self.client.get('/api/v1/auth/me/').status_code, 404)

    def test_suspended_context_is_forbidden(self):
        self.membership_b.status='suspended'; self.membership_b.save(); self.auth(membership=self.membership_b)
        self.assertEqual(self.client.get('/api/v1/auth/me/').status_code, 403)

    def test_ended_context_is_forbidden(self):
        self.membership_b.status='ended'; self.membership_b.save(); self.auth(membership=self.membership_b)
        self.assertEqual(self.client.get('/api/v1/auth/me/').status_code, 403)

    def test_inactive_school_context_is_forbidden(self):
        self.school_b.is_active=False; self.school_b.save(); self.auth(membership=self.membership_b)
        self.assertEqual(self.client.get('/api/v1/auth/me/').status_code, 403)

    def test_historical_context_allows_get(self):
        self.membership_b.status='historical'; self.membership_b.save(); self.auth(membership=self.membership_b)
        self.assertEqual(self.client.get('/api/v1/auth/context/').status_code, 200)

    def test_historical_context_blocks_post(self):
        self.membership_b.status='historical'; self.membership_b.save(); self.auth(membership=self.membership_b)
        self.assertEqual(self.client.post('/api/v1/attendance/', {}).status_code, 403)

    def test_historical_context_blocks_put(self):
        self.membership_b.status='historical'; self.membership_b.save(); self.auth(membership=self.membership_b)
        self.assertEqual(self.client.put('/api/v1/attendance/999/', {}).status_code, 403)

    def test_historical_context_blocks_patch(self):
        self.membership_b.status='historical'; self.membership_b.save(); self.auth(membership=self.membership_b)
        self.assertEqual(self.client.patch('/api/v1/attendance/999/', {}).status_code, 403)

    def test_historical_context_blocks_delete(self):
        self.membership_b.status='historical'; self.membership_b.save(); self.auth(membership=self.membership_b)
        self.assertEqual(self.client.delete('/api/v1/attendance/999/').status_code, 403)

    def test_context_list_includes_both_active_memberships(self):
        self.auth(membership=self.membership_a); response=self.client.get('/api/v1/auth/contexts/')
        self.assertEqual(len(response.data['contexts']), 2)

    def test_context_control_endpoints_ignore_stale_membership_header(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.user).access_token}',
            HTTP_X_SCHOOL_MEMBERSHIP_ID='999999',
        )
        contexts = self.client.get('/api/v1/auth/contexts/')
        self.assertEqual(contexts.status_code, 200)
        self.assertEqual(len(contexts.data['contexts']), 2)
        changed = self.client.post(
            '/api/v1/auth/context/default/',
            {'membership_id': self.membership_b.pk},
            format='json',
        )
        self.assertEqual(changed.status_code, 200)

    def test_default_context_can_be_changed(self):
        self.auth(membership=self.membership_a)
        response=self.client.post('/api/v1/auth/context/default/', {'membership_id': self.membership_b.pk}, format='json')
        self.assertEqual(response.status_code, 200); self.membership_b.refresh_from_db(); self.assertTrue(self.membership_b.is_default)
    def test_context_serializer_without_request_resolves_school_year(self):
        from .context_serializers import SchoolMembershipSerializer
        data = SchoolMembershipSerializer(self.membership_a).data
        self.assertEqual(data['academic_year']['id'], self.year_a.pk)

    def test_context_serializer_marks_inactive_school_unavailable(self):
        from .context_serializers import SchoolMembershipSerializer
        self.school_b.is_active = False
        self.school_b.save()
        data = SchoolMembershipSerializer(self.membership_b).data
        self.assertEqual(data['access_mode'], 'unavailable')
        self.assertFalse(data['can_write'])

    def test_default_context_rejects_inactive_and_foreign_memberships(self):
        self.school_b.is_active = False
        self.school_b.save()
        self.auth(membership=self.membership_a)
        inactive = self.client.post('/api/v1/auth/context/default/', {'membership_id': self.membership_b.pk}, format='json')
        foreign = self.client.post('/api/v1/auth/context/default/', {'membership_id': self.student_membership.pk}, format='json')
        self.assertEqual(inactive.status_code, 400)
        self.assertEqual(foreign.status_code, 400)