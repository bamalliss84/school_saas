from datetime import date
from unittest.mock import patch

from django.test import TestCase
from rest_framework import status

from .models import HomeworkActionLog, SchoolMembership, StudentEnrollment, User
from .services.identity import transfer_student
from .test_sprint4d_memberships import Sprint4DFixtureMixin


class StudentTransferTests(Sprint4DFixtureMixin, TestCase):
    def payload(self):
        return {'destination_school': self.school_b.pk, 'destination_academic_year': self.year_b.pk, 'destination_classroom': self.class_b.pk, 'destination_section': self.section_b.pk, 'transfer_date': '2026-06-01', 'reason': 'Family relocation'}

    def transfer(self):
        return transfer_student(student=self.student, destination_school=self.school_b, destination_academic_year=self.year_b, destination_classroom=self.class_b, destination_section=self.section_b, transfer_date=date(2026,6,1), actor=self.super_admin, reason='Family relocation')

    def test_super_admin_transfer_endpoint_succeeds(self):
        self.auth(self.super_admin); response=self.client.post(f'/api/v1/students/{self.student.pk}/transfer/', self.payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_old_enrollment_is_closed(self):
        self.transfer(); self.enrollment.refresh_from_db(); self.assertFalse(self.enrollment.is_current); self.assertEqual(self.enrollment.status, 'transferred')

    def test_old_enrollment_end_date_is_set(self):
        self.transfer(); self.enrollment.refresh_from_db(); self.assertEqual(self.enrollment.end_date, date(2026,6,1))

    def test_old_student_membership_becomes_historical(self):
        self.transfer(); self.student_membership.refresh_from_db(); self.assertEqual(self.student_membership.status, 'historical')

    def test_destination_membership_is_active(self):
        self.transfer(); self.assertTrue(SchoolMembership.objects.filter(user=self.student_user, school=self.school_b, role='student', status='active').exists())

    def test_destination_membership_is_default(self):
        self.transfer(); self.assertTrue(SchoolMembership.objects.get(user=self.student_user, school=self.school_b, role='student').is_default)

    def test_new_enrollment_is_current(self):
        destination=self.transfer(); self.assertTrue(destination.is_current); self.assertEqual(destination.status, 'active')

    def test_legacy_student_school_is_updated(self):
        self.transfer(); self.student.refresh_from_db(); self.assertEqual(self.student.school, self.school_b)

    def test_transfer_writes_audit_event(self):
        self.transfer(); self.assertTrue(HomeworkActionLog.objects.filter(action='student_transfer', entity_id=self.student.pk).exists())

    def test_transfer_does_not_delete_old_enrollment(self):
        old_pk=self.enrollment.pk; self.transfer(); self.assertTrue(StudentEnrollment.objects.filter(pk=old_pk).exists())

    def test_non_super_admin_cannot_transfer(self):
        self.auth(membership=self.membership_a); response=self.client.post(f'/api/v1/students/{self.student.pk}/transfer/', self.payload(), format='json')
        self.assertEqual(response.status_code, 403)

    def test_same_school_destination_is_rejected(self):
        with self.assertRaises(Exception):
            transfer_student(student=self.student, destination_school=self.school_a, destination_academic_year=self.year_a, destination_classroom=self.class_a, destination_section=self.section_a, transfer_date=date(2026,6,1), actor=self.super_admin, reason='Invalid')

    def test_invalid_cross_school_relations_are_rejected(self):
        data=self.payload(); data['destination_classroom']=self.class_a.pk; self.auth(self.super_admin)
        self.assertEqual(self.client.post(f'/api/v1/students/{self.student.pk}/transfer/', data, format='json').status_code, 400)

    def test_failure_rolls_back_all_transfer_changes(self):
        with patch('core.services.identity.HomeworkActionLog.objects.create', side_effect=RuntimeError('audit unavailable')):
            with self.assertRaises(RuntimeError): self.transfer()
        self.enrollment.refresh_from_db(); self.student.refresh_from_db(); self.assertTrue(self.enrollment.is_current); self.assertEqual(self.student.school, self.school_a)
    def test_transfer_updates_guardian_memberships(self):
        parent_user = User.objects.create_user(username='transfer-parent', password=None, role='parent', school=self.school_a)
        from .models import Parent, StudentGuardian
        parent = Parent.objects.create(user=parent_user, school=self.school_a, full_name='Transfer Parent')
        StudentGuardian.objects.create(parent=parent, student=self.student, relationship='guardian')
        SchoolMembership.objects.create(user=parent_user, school=self.school_a, role='parent', status='active', is_default=True)
        self.transfer()
        self.assertTrue(SchoolMembership.objects.filter(user=parent_user, school=self.school_b, role='parent', status='active').exists())
        self.assertEqual(SchoolMembership.objects.get(user=parent_user, school=self.school_a, role='parent').status, 'historical')