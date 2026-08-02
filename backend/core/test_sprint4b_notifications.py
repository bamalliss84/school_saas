from datetime import timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework import status

from .models import Notification, SchoolMembership
from .services.notifications import create_notification, create_notifications_bulk
from .test_sprint4d_memberships import Sprint4DFixtureMixin


class Sprint4BNotificationTests(Sprint4DFixtureMixin, TestCase):
    def notification(self, membership=None, key=''):
        membership = membership or self.membership_a
        return create_notification(
            recipient_membership=membership, notification_type='system', title='Notice',
            body='Safe body', payload={'action': {'route': 'school', 'params': {}}},
            deduplication_key=key,
        )

    def test_model_accepts_consistent_notification(self):
        item = self.notification(); item.full_clean(); self.assertEqual(item.recipient, self.user)

    def test_model_rejects_recipient_mismatch(self):
        item = Notification(school=self.school_a, recipient=self.student_user, recipient_membership=self.membership_a, notification_type='system', title='x')
        with self.assertRaises(DjangoValidationError): item.full_clean()

    def test_model_rejects_school_mismatch(self):
        item = Notification(school=self.school_b, recipient=self.user, recipient_membership=self.membership_a, notification_type='system', title='x')
        with self.assertRaises(DjangoValidationError): item.full_clean()

    def test_database_rejects_read_without_timestamp(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Notification.objects.create(school=self.school_a, recipient=self.user, recipient_membership=self.membership_a, notification_type='system', title='x', is_read=True)

    def test_database_rejects_timestamp_when_unread(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Notification.objects.create(school=self.school_a, recipient=self.user, recipient_membership=self.membership_a, notification_type='system', title='x', read_at=timezone.now())

    def test_deduplication_service_returns_existing(self):
        first=self.notification(key='stable'); second=self.notification(key='stable'); self.assertEqual(first.pk, second.pk)

    def test_database_deduplication_constraint(self):
        self.notification(key='stable')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Notification.objects.create(school=self.school_a, recipient=self.user, recipient_membership=self.membership_a, notification_type='system', title='x', deduplication_key='stable')

    def test_same_key_allowed_for_other_membership(self):
        self.notification(key='stable'); self.notification(self.membership_b, key='stable'); self.assertEqual(Notification.objects.count(), 2)

    def test_suspended_recipient_rejected(self):
        self.membership_a.is_default=False; self.membership_a.status='suspended'; self.membership_a.save()
        with self.assertRaises(Exception): self.notification()

    def test_ended_recipient_rejected(self):
        self.membership_a.is_default=False; self.membership_a.status='ended'; self.membership_a.save()
        with self.assertRaises(Exception): self.notification()

    def test_historical_recipient_rejected(self):
        self.membership_a.is_default=False; self.membership_a.status='historical'; self.membership_a.save()
        with self.assertRaises(Exception): self.notification()

    def test_inactive_school_recipient_rejected(self):
        self.school_a.is_active=False; self.school_a.save()
        with self.assertRaises(Exception): self.notification()

    def test_bulk_skips_unavailable_memberships(self):
        self.membership_b.status='suspended'; self.membership_b.save()
        rows=create_notifications_bulk(memberships=(self.membership_a,self.membership_b), notification_type='system', title='x')
        self.assertEqual(len(rows),1)

    def test_list_is_active_membership_scoped(self):
        own=self.notification(self.membership_a); self.notification(self.membership_b); self.auth(membership=self.membership_a)
        response=self.client.get('/api/v1/notifications/'); self.assertEqual(response.status_code,200); self.assertEqual([row['id'] for row in response.data['results']],[own.pk])

    def test_same_user_other_context_detail_is_404(self):
        other=self.notification(self.membership_b); self.auth(membership=self.membership_a)
        self.assertEqual(self.client.get(f'/api/v1/notifications/{other.pk}/').status_code,404)

    def test_unauthenticated_list_is_401(self):
        self.assertEqual(self.client.get('/api/v1/notifications/').status_code,401)

    def test_multiple_contexts_without_header_is_409(self):
        self.notification(); self.auth(); self.assertEqual(self.client.get('/api/v1/notifications/').status_code,409)

    def test_read_sets_timestamp(self):
        item=self.notification(); self.auth(membership=self.membership_a); response=self.client.post(f'/api/v1/notifications/{item.pk}/read/')
        item.refresh_from_db(); self.assertEqual(response.status_code,200); self.assertTrue(item.is_read); self.assertIsNotNone(item.read_at)

    def test_read_is_idempotent(self):
        item=self.notification(); self.auth(membership=self.membership_a); url=f'/api/v1/notifications/{item.pk}/read/'; self.client.post(url); item.refresh_from_db(); first=item.read_at; self.client.post(url); item.refresh_from_db(); self.assertEqual(item.read_at,first)

    def test_historical_context_allows_personal_read(self):
        item=self.notification(); self.membership_a.status='historical'; self.membership_a.is_default=False; self.membership_a.save(); self.auth(membership=self.membership_a)
        self.assertEqual(self.client.post(f'/api/v1/notifications/{item.pk}/read/').status_code,200)

    def test_read_all_only_changes_active_membership(self):
        own=self.notification(self.membership_a); other=self.notification(self.membership_b); self.auth(membership=self.membership_a); response=self.client.post('/api/v1/notifications/read-all/')
        own.refresh_from_db(); other.refresh_from_db(); self.assertEqual(response.data['updated_count'],1); self.assertTrue(own.is_read); self.assertFalse(other.is_read)

    def test_unread_count_returns_membership(self):
        self.notification(); self.notification(); self.auth(membership=self.membership_a); response=self.client.get('/api/v1/notifications/unread-count/')
        self.assertEqual(response.data, {'membership_id':self.membership_a.pk,'unread_count':2})

    def test_filters_and_ordering(self):
        self.notification(); create_notification(recipient_membership=self.membership_a,notification_type='homework_graded',title='Grade'); self.auth(membership=self.membership_a)
        response=self.client.get('/api/v1/notifications/', {'notification_type':'homework_graded','ordering':'created_at'}); self.assertEqual(response.data['count'],1)

    def test_invalid_ordering_is_400(self):
        self.auth(membership=self.membership_a); self.assertEqual(self.client.get('/api/v1/notifications/', {'ordering':'title'}).status_code,400)

    def test_invalid_date_range_is_400(self):
        self.auth(membership=self.membership_a); now=timezone.now(); response=self.client.get('/api/v1/notifications/', {'date_from':now.isoformat(),'date_to':(now-timedelta(days=1)).isoformat()}); self.assertEqual(response.status_code,400)

    def test_no_public_create_update_delete(self):
        item=self.notification(); self.auth(membership=self.membership_a)
        self.assertEqual(self.client.post('/api/v1/notifications/',{}).status_code,405); self.assertEqual(self.client.patch(f'/api/v1/notifications/{item.pk}/',{}).status_code,405); self.assertEqual(self.client.delete(f'/api/v1/notifications/{item.pk}/').status_code,405)

    def test_contexts_include_unread_counts_without_n_plus_one(self):
        self.notification(self.membership_a); self.notification(self.membership_b); self.auth(membership=self.membership_a)
        with self.assertNumQueries(8): response=self.client.get('/api/v1/auth/contexts/')
        counts={row['membership_id']:row['unread_notifications_count'] for row in response.data['contexts']}; self.assertEqual(counts,{self.membership_a.pk:1,self.membership_b.pk:1})

    def test_compatibility_route_works(self):
        self.auth(membership=self.membership_a); self.assertEqual(self.client.get('/api/notifications/').status_code,200)

    def test_openapi_has_notification_paths(self):
        self.super_admin.is_staff=True; self.super_admin.save(); self.auth(user=self.super_admin); response=self.client.get('/api/schema/'); text=response.content.decode(); self.assertIn('/api/v1/notifications/',text)