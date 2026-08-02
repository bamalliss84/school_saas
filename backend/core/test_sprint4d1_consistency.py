from datetime import date, timedelta
from importlib import import_module

from django.apps import apps
from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework import status

from .models import (
    AcademicTerm, Homework, HomeworkSubmission, Parent, SchoolMembership,
    StudentEnrollment, StudentGuardian, TeacherAssignment, User,
)
from .services.identity import (
    set_current_student_enrollment, sync_legacy_user_context, sync_parent_memberships,
    sync_student_memberships, sync_teacher_memberships,
)
from .test_sprint4d_memberships import Sprint4DFixtureMixin


class Sprint4DConsistencyTests(Sprint4DFixtureMixin, TestCase):
    def transfer_payload(self, **changes):
        payload = {
            'destination_school': self.school_b.pk,
            'destination_academic_year': self.year_b.pk,
            'destination_classroom': self.class_b.pk,
            'destination_section': self.section_b.pk,
            'transfer_date': '2026-06-01',
            'reason': 'Consistency test',
        }
        payload.update(changes)
        return payload

    def call_transfer(self, **changes):
        self.auth(self.super_admin)
        return self.client.post(
            f'/api/v1/students/{self.student.pk}/transfer/',
            self.transfer_payload(**changes), format='json',
        )

    def test_migration_prefers_current_enrollment_over_stale_user_school(self):
        self.enrollment.is_current = False
        self.enrollment.status = 'transferred'
        self.enrollment.save()
        current = StudentEnrollment.objects.create(
            student=self.student, school=self.school_b, academic_year=self.year_b,
            classroom=self.class_b, section=self.section_b, status='active', is_current=True,
        )
        User.objects.filter(pk=self.student_user.pk).update(school=self.school_a, academic_year=self.year_a)
        SchoolMembership.objects.filter(user=self.student_user).delete()
        migration = import_module('core.migrations.0020_multischool_memberships')
        migration.populate_school_memberships(apps, None)
        migration.populate_school_memberships(apps, None)
        memberships = SchoolMembership.objects.filter(user=self.student_user, role='student')
        self.assertEqual(memberships.filter(status='active').count(), 1)
        self.assertTrue(memberships.get(school=self.school_b).is_default)
        self.assertEqual(memberships.get(school=self.school_a).status, 'historical')
        current.refresh_from_db()
        self.assertTrue(current.is_current)

    def test_sync_student_updates_all_legacy_pointers(self):
        self.enrollment.is_current = False
        self.enrollment.status = 'transferred'
        self.enrollment.save()
        destination = StudentEnrollment.objects.create(
            student=self.student, school=self.school_b, academic_year=self.year_b,
            classroom=self.class_b, section=self.section_b, status='active', is_current=True,
        )
        sync_student_memberships(self.student)
        self.student.refresh_from_db(); self.student_user.refresh_from_db()
        self.assertEqual(self.student.school, self.school_b)
        self.assertEqual(self.student_user.school, self.school_b)
        self.assertEqual(self.student_user.academic_year, self.year_b)
        self.assertTrue(SchoolMembership.objects.get(user=self.student_user, school=self.school_b, role='student').is_default)
        self.assertTrue(destination.is_current)

    def test_set_current_enrollment_switches_atomically(self):
        self.enrollment.is_current = False; self.enrollment.status = 'transferred'; self.enrollment.save()
        destination = StudentEnrollment.objects.create(
            student=self.student, school=self.school_b, academic_year=self.year_b,
            classroom=self.class_b, section=self.section_b, status='transferred', is_current=False,
        )
        set_current_student_enrollment(destination)
        destination.refresh_from_db()
        self.assertTrue(destination.is_current); self.assertEqual(destination.status, 'active')

    def test_parent_sync_keeps_school_active_for_another_current_child(self):
        parent_user = User.objects.create_user(username='parent-sync', password=None, role='parent', school=self.school_a)
        parent = Parent.objects.create(user=parent_user, school=self.school_a, full_name='Parent Sync')
        StudentGuardian.objects.create(parent=parent, student=self.student, relationship='guardian')
        sync_parent_memberships(parent=parent)
        self.assertEqual(SchoolMembership.objects.get(user=parent_user, school=self.school_a, role='parent').status, 'active')

    def test_parent_guardian_removal_makes_history_only_membership_historical(self):
        parent_user = User.objects.create_user(username='parent-history', password=None, role='parent', school=self.school_a)
        parent = Parent.objects.create(user=parent_user, school=self.school_a, full_name='Parent History')
        link = StudentGuardian.objects.create(parent=parent, student=self.student, relationship='guardian')
        sync_parent_memberships(parent=parent)
        self.enrollment.is_current=False; self.enrollment.status='transferred'; self.enrollment.save()
        sync_parent_memberships(parent=parent)
        self.assertEqual(SchoolMembership.objects.get(user=parent_user, school=self.school_a, role='parent').status, 'historical')
        link.delete(); sync_parent_memberships(parent=parent)

    def test_teacher_sync_creates_current_assignment_membership(self):
        self.membership_b.delete()
        TeacherAssignment.objects.bulk_create([TeacherAssignment(
            teacher=self.teacher, school=self.school_b, academic_year=self.year_b,
            classroom=self.class_b, section=self.section_b, subject=self.subject_b,
        )])
        saved = sync_teacher_memberships(self.teacher)
        self.assertTrue(any(item.school_id == self.school_b.pk and item.status == 'active' for item in saved))

    def test_teacher_sync_does_not_downgrade_explicit_active_membership(self):
        TeacherAssignment.objects.filter(teacher=self.teacher, school=self.school_b).update(is_current=False)
        sync_teacher_memberships(self.teacher)
        self.membership_b.refresh_from_db()
        self.assertEqual(self.membership_b.status, 'active')

    def test_transfer_updates_user_legacy_context(self):
        self.assertEqual(self.call_transfer().status_code, 201)
        self.student_user.refresh_from_db()
        self.assertEqual(self.student_user.school, self.school_b)
        self.assertEqual(self.student_user.academic_year, self.year_b)

    def test_transfer_preserves_other_role_membership(self):
        other = SchoolMembership.objects.create(user=self.student_user, school=self.school_a, role='parent', status='active')
        self.assertEqual(self.call_transfer().status_code, 201)
        other.refresh_from_db(); self.assertEqual(other.status, 'active')

    def test_login_after_transfer_uses_new_default_context(self):
        self.student_user.set_password('Transfer-login-password-123'); self.student_user.save()
        self.assertEqual(self.call_transfer().status_code, 201)
        self.client.credentials()
        response = self.client.post('/api/auth/login/', {'username': self.student_user.username, 'password': 'Transfer-login-password-123'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['default_membership_id'], SchoolMembership.objects.get(user=self.student_user, school=self.school_b, role='student').pk)

    def test_transfer_rejects_inactive_school(self):
        self.school_b.is_active=False; self.school_b.save()
        self.assertEqual(self.call_transfer().status_code, 400)

    def test_transfer_rejects_inactive_year(self):
        self.year_b.is_active=False; self.year_b.save()
        self.assertEqual(self.call_transfer().status_code, 400)

    def test_transfer_rejects_inactive_classroom_and_section(self):
        self.class_b.is_active=False; self.class_b.save()
        self.assertEqual(self.call_transfer().status_code, 400)
        self.class_b.is_active=True; self.class_b.save(); self.section_b.is_active=False; self.section_b.save()
        self.assertEqual(self.call_transfer().status_code, 400)

    def test_transfer_rejects_date_before_current_start(self):
        self.enrollment.start_date=date(2026,7,1); self.enrollment.save()
        self.assertEqual(self.call_transfer().status_code, 400)

    def test_transfer_rejects_date_outside_destination_year_and_rolls_back(self):
        response=self.call_transfer(transfer_date='2027-01-01')
        self.assertEqual(response.status_code, 400)
        self.enrollment.refresh_from_db(); self.assertTrue(self.enrollment.is_current)

    def test_access_mode_is_centralized_for_all_states(self):
        self.assertEqual(self.membership_b.access_mode, 'read_write')
        self.membership_b.status='historical'; self.membership_b.save(); self.assertEqual(self.membership_b.access_mode, 'read_only')
        self.membership_b.status='suspended'; self.membership_b.save(); self.assertEqual(self.membership_b.access_mode, 'unavailable')
        self.membership_b.status='ended'; self.membership_b.save(); self.assertFalse(self.membership_b.can_read)

    def test_context_get_does_not_write_last_used_at_or_legacy_database_fields(self):
        original_school=self.user.school_id; original_role=self.user.role
        self.auth(membership=self.membership_b)
        self.assertEqual(self.client.get('/api/v1/auth/context/').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/auth/context/').status_code, 200)
        self.membership_b.refresh_from_db(); self.user.refresh_from_db()
        self.assertIsNone(self.membership_b.last_used_at)
        self.assertEqual(self.user.school_id, original_school); self.assertEqual(self.user.role, original_role)

    def test_default_context_updates_last_used_at(self):
        self.auth(membership=self.membership_a)
        response=self.client.post('/api/v1/auth/context/default/', {'membership_id': self.membership_b.pk}, format='json')
        self.assertEqual(response.status_code, 200)
        self.membership_b.refresh_from_db(); self.assertIsNotNone(self.membership_b.last_used_at)

    def test_sync_legacy_context_from_membership_and_restore_adapter(self):
        from .context import apply_membership_context, restore_legacy_user_context
        from rest_framework.test import APIRequestFactory
        sync_legacy_user_context(self.user, membership=self.membership_b)
        self.user.refresh_from_db(); self.assertEqual(self.user.school, self.school_b)
        original_role = self.user.role
        request = APIRequestFactory().get('/api/v1/auth/context/')
        request.query_params = request.GET
        apply_membership_context(request, self.user, self.membership_a)
        restore_legacy_user_context(self.user)
        self.assertEqual(self.user.school_id, self.school_b.pk); self.assertEqual(self.user.role, original_role)

    def test_student_without_user_still_syncs_legacy_student_school(self):
        from .models import Student
        student = Student.objects.create(school=self.school_a, full_name='No account', gender='female')
        StudentEnrollment.objects.create(student=student, school=self.school_b, academic_year=self.year_b, classroom=self.class_b, section=self.section_b, status='active', is_current=True)
        sync_student_memberships(student)
        student.refresh_from_db(); self.assertEqual(student.school, self.school_b)

    def test_parent_sync_accepts_student_and_skips_parent_without_user(self):
        parent = Parent.objects.create(school=self.school_a, full_name='No account parent')
        StudentGuardian.objects.create(parent=parent, student=self.student, relationship='guardian')
        result = sync_parent_memberships(student=self.student)
        self.assertIn(parent, result)
        self.assertFalse(SchoolMembership.objects.filter(role='parent', school=self.school_a, user__isnull=True).exists())

    def test_teacher_sync_handles_no_user_and_historical_assignment(self):
        from .models import Teacher
        teacher = Teacher.objects.create(school=self.school_a, academic_year=self.year_a, full_name='No account teacher', employee_code='NOUSER-T99999')
        self.assertEqual(sync_teacher_memberships(teacher), [])
        self.membership_b.delete()
        TeacherAssignment.objects.bulk_create([TeacherAssignment(
            teacher=self.teacher, school=self.school_b, academic_year=self.year_b,
            classroom=self.class_b, section=self.section_b, subject=self.subject_b,
            is_current=False,
        )])
        sync_teacher_memberships(self.teacher)
        self.assertEqual(SchoolMembership.objects.get(user=self.user, school=self.school_b, role='teacher').status, 'historical')

    def test_transfer_rejects_missing_current_and_unsafe_existing_destination(self):
        self.enrollment.is_current=False; self.enrollment.status='transferred'; self.enrollment.save()
        self.assertEqual(self.call_transfer().status_code, 400)
        self.enrollment.is_current=True; self.enrollment.status='active'; self.enrollment.save()
        StudentEnrollment.objects.create(student=self.student, school=self.school_b, academic_year=self.year_b, classroom=self.class_b, section=self.section_b, status='active', is_current=False)
        self.assertEqual(self.call_transfer().status_code, 400)
    def test_inactive_school_makes_even_active_membership_unavailable(self):
        self.school_b.is_active = False
        self.school_b.save()
        self.membership_b.refresh_from_db()
        self.assertEqual(self.membership_b.access_mode, 'unavailable')
        self.assertFalse(self.membership_b.can_read)
        self.assertFalse(self.membership_b.can_write)

    def test_membership_serializer_uses_central_access_policy(self):
        from .context_serializers import SchoolMembershipSerializer
        self.membership_b.status = 'suspended'
        self.membership_b.save()
        payload = SchoolMembershipSerializer(self.membership_b).data
        self.assertEqual(payload['access_mode'], 'unavailable')
        self.assertFalse(payload['can_write'])
    def test_admin_service_validation_returns_message_without_500(self):
        from django.contrib import admin, messages
        from django.contrib.messages import get_messages
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory
        from rest_framework.exceptions import ValidationError
        from .admin import StudentEnrollmentAdmin
        request = RequestFactory().post('/admin/core/studentenrollment/add/')
        request.user = self.super_admin
        request.session = self.client.session
        request._messages = FallbackStorage(request)
        model_admin = StudentEnrollmentAdmin(StudentEnrollment, admin.site)
        response = model_admin._safe_admin_mutation(
            request, lambda: (_ for _ in ()).throw(ValidationError('Invalid enrollment.')),
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(any(message.level == messages.ERROR for message in get_messages(request)))
    def test_student_sync_without_current_makes_student_memberships_historical(self):
        self.enrollment.is_current = False
        self.enrollment.status = 'transferred'
        self.enrollment.save()
        self.assertIsNone(sync_student_memberships(self.student))
        self.student_membership.refresh_from_db()
        self.assertEqual(self.student_membership.status, 'historical')
        self.assertFalse(self.student_membership.is_default)

    def test_parent_sync_reactivates_existing_historical_membership(self):
        parent_user = User.objects.create_user(username='reactivate-parent', password=None, role='parent', school=self.school_a)
        parent = Parent.objects.create(user=parent_user, school=self.school_a, full_name='Reactivate Parent')
        StudentGuardian.objects.create(parent=parent, student=self.student, relationship='guardian')
        membership = SchoolMembership.objects.create(user=parent_user, school=self.school_a, role='parent', status='historical')
        sync_parent_memberships(parent=parent)
        membership.refresh_from_db()
        self.assertEqual(membership.status, 'active')

    def test_teacher_sync_reactivates_derived_historical_membership(self):
        self.membership_b.status = 'historical'
        self.membership_b.save()
        TeacherAssignment.objects.bulk_create([TeacherAssignment(
            teacher=self.teacher, school=self.school_b, academic_year=self.year_b,
            classroom=self.class_b, section=self.section_b, subject=self.subject_b,
            is_current=True,
        )])
        sync_teacher_memberships(self.teacher)
        self.membership_b.refresh_from_db()
        self.assertEqual(self.membership_b.status, 'active')

class HistoricalHomeworkTests(Sprint4DFixtureMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.enrollment_b = StudentEnrollment.objects.create(
            student=self.student, school=self.school_b, academic_year=self.year_b,
            classroom=self.class_b, section=self.section_b, status='transferred', is_current=False,
        )
        self.student_history = SchoolMembership.objects.create(
            user=self.student_user, school=self.school_b, role='student', status='historical',
        )
        self.assignment_b = TeacherAssignment.objects.create(
            teacher=self.teacher, school=self.school_b, academic_year=self.year_b,
            classroom=self.class_b, section=self.section_b, subject=self.subject_b,
        )
        self.term_b = AcademicTerm.objects.create(
            school=self.school_b, academic_year=self.year_b, name='Old term', term_type='term_1',
            start_date=self.year_b.start_date, end_date=self.year_b.end_date,
        )
        self.published = Homework.objects.create(
            school=self.school_b, academic_year=self.year_b, academic_term=self.term_b,
            teacher_assignment=self.assignment_b, title='Historical published', status='published',
            published_at=timezone.now(), due_date=timezone.now()+timedelta(days=1), created_by=self.super_admin,
        )
        self.draft = Homework.objects.create(
            school=self.school_b, academic_year=self.year_b, academic_term=self.term_b,
            teacher_assignment=self.assignment_b, title='Historical draft', status='draft',
            due_date=timezone.now()+timedelta(days=1), created_by=self.super_admin,
        )
        self.submission = HomeworkSubmission.objects.create(
            homework=self.published, student_enrollment=self.enrollment_b, answer='Old answer', status='submitted', submitted_at=timezone.now(),
        )

    def test_student_reads_published_historical_homework_not_draft(self):
        self.auth(self.student_user, self.student_history)
        response=self.client.get('/api/v1/homework/')
        ids={row['id'] for row in response.data['results']}
        request_user = response.wsgi_request.user
        from .homework_selectors import _enrollment_scope, homework_for_user
        self.assertEqual(request_user.school_id, self.school_b.pk)
        self.assertEqual(_enrollment_scope(request_user).count(), 1)
        self.assertTrue(homework_for_user(request_user).filter(pk=self.published.pk).exists())
        from .homework_serializers import HomeworkQuerySerializer
        from .homework_views import _filter_homework
        query = HomeworkQuerySerializer(data={}); query.is_valid(raise_exception=True)
        self.assertTrue(_filter_homework(homework_for_user(request_user), query.validated_data, request_user).filter(pk=self.published.pk).exists())
        self.assertIn(self.published.pk, ids, response.data); self.assertNotIn(self.draft.pk, ids)

    def test_student_reads_historical_submission(self):
        self.auth(self.student_user, self.student_history)
        response=self.client.get('/api/v1/homework-submissions/')
        self.assertIn(self.submission.pk, {row['id'] for row in response.data['results']})

    def test_historical_student_cannot_submit(self):
        self.auth(self.student_user, self.student_history)
        self.assertEqual(self.client.post('/api/v1/homework/', {}, format='json').status_code, 403)

    def test_historical_filter_cannot_expand_school(self):
        self.auth(self.student_user, self.student_history)
        response=self.client.get(f'/api/v1/homework/?academic_year_id={self.year_a.pk}')
        self.assertEqual(response.status_code, 404)

    def test_parent_reads_child_historical_homework_only_when_guardian(self):
        parent_user=User.objects.create_user(username='historical-parent', password=None, role='parent', school=self.school_a)
        parent=Parent.objects.create(user=parent_user, school=self.school_a, full_name='Historical Parent')
        StudentGuardian.objects.create(parent=parent, student=self.student, relationship='guardian')
        membership=SchoolMembership.objects.create(user=parent_user, school=self.school_b, role='parent', status='historical')
        self.auth(parent_user, membership)
        response=self.client.get('/api/v1/homework/')
        self.assertIn(self.published.pk, {row['id'] for row in response.data['results']}, response.data)