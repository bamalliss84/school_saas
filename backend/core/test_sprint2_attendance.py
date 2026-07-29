from datetime import date

from django.db import IntegrityError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import (
    AcademicTerm, AcademicYear, Attendance, Classroom, Parent, School, Section,
    Student, StudentEnrollment, StudentGuardian, Subject, Teacher,
    TeacherAssignment, User,
)


class SprintTwoAttendanceAPITestCase(APITestCase):
    password = 'Strong-test-password-123'
    day = date(2026, 7, 29)

    @classmethod
    def setUpTestData(cls):
        cls.school_a = School.objects.create(name='Attendance A', code='ATA')
        cls.school_b = School.objects.create(name='Attendance B', code='ATB')
        cls.year_a = AcademicYear.objects.create(
            school=cls.school_a, name='2026 A', start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        )
        cls.year_b = AcademicYear.objects.create(
            school=cls.school_b, name='2026 B', start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        )
        cls.term_a = AcademicTerm.objects.create(
            school=cls.school_a, academic_year=cls.year_a, name='Term A', term_type='term_1',
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        )
        cls.term_b = AcademicTerm.objects.create(
            school=cls.school_b, academic_year=cls.year_b, name='Term B', term_type='term_1',
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        )
        cls.class_a = Classroom.objects.create(school=cls.school_a, academic_year=cls.year_a, name='Grade A', code='GA')
        cls.section_a = Section.objects.create(school=cls.school_a, academic_year=cls.year_a, classroom=cls.class_a, name='A', code='A')
        cls.class_other = Classroom.objects.create(school=cls.school_a, academic_year=cls.year_a, name='Grade Other', code='GO')
        cls.section_other = Section.objects.create(school=cls.school_a, academic_year=cls.year_a, classroom=cls.class_other, name='O', code='O')
        cls.class_b = Classroom.objects.create(school=cls.school_b, academic_year=cls.year_b, name='Grade B', code='GB')
        cls.section_b = Section.objects.create(school=cls.school_b, academic_year=cls.year_b, classroom=cls.class_b, name='B', code='B')
        cls.subject_a = Subject.objects.create(school=cls.school_a, name='Math', code='M')
        cls.subject_b = Subject.objects.create(school=cls.school_b, name='Math', code='M')

        cls.super_admin = cls.user('att-super', 'super_admin', None, None)
        cls.admin_a = cls.user('att-admin-a', 'school_admin', cls.school_a, cls.year_a)
        cls.admin_b = cls.user('att-admin-b', 'school_admin', cls.school_b, cls.year_b)
        cls.teacher_user = cls.user('att-teacher', 'teacher', cls.school_a, cls.year_a)
        cls.teacher_other_user = cls.user('att-teacher-other', 'teacher', cls.school_a, cls.year_a)
        cls.parent_user = cls.user('att-parent', 'parent', cls.school_a, cls.year_a)
        cls.parent_other_user = cls.user('att-parent-other', 'parent', cls.school_a, cls.year_a)
        cls.student_user = cls.user('att-student', 'student', cls.school_a, cls.year_a)
        cls.student_other_user = cls.user('att-student-other', 'student', cls.school_a, cls.year_a)

        cls.teacher = Teacher.objects.create(school=cls.school_a, academic_year=cls.year_a, user=cls.teacher_user, full_name='Teacher A', employee_code='ATA-T90001')
        cls.teacher_other = Teacher.objects.create(school=cls.school_a, academic_year=cls.year_a, user=cls.teacher_other_user, full_name='Teacher Other', employee_code='ATA-T90002')
        cls.teacher_b = Teacher.objects.create(school=cls.school_b, academic_year=cls.year_b, full_name='Teacher B', employee_code='ATB-T90001')
        cls.parent = Parent.objects.create(school=cls.school_a, user=cls.parent_user, full_name='Parent A', parent_code='ATA-P90001')
        cls.parent_other = Parent.objects.create(school=cls.school_a, user=cls.parent_other_user, full_name='Parent Other', parent_code='ATA-P90002')

        cls.student = Student.objects.create(school=cls.school_a, user=cls.student_user, full_name='Student A', gender='male')
        cls.student_peer = Student.objects.create(school=cls.school_a, full_name='Student Peer', gender='female')
        cls.student_other = Student.objects.create(school=cls.school_a, user=cls.student_other_user, full_name='Student Other', gender='male')
        cls.student_b = Student.objects.create(school=cls.school_b, full_name='Student B', gender='female')
        cls.enrollment = cls.enroll(cls.student, cls.school_a, cls.year_a, cls.class_a, cls.section_a)
        cls.enrollment_peer = cls.enroll(cls.student_peer, cls.school_a, cls.year_a, cls.class_a, cls.section_a)
        cls.enrollment_other = cls.enroll(cls.student_other, cls.school_a, cls.year_a, cls.class_other, cls.section_other)
        cls.enrollment_b = cls.enroll(cls.student_b, cls.school_b, cls.year_b, cls.class_b, cls.section_b)
        StudentGuardian.objects.create(student=cls.student, parent=cls.parent, relationship='father')
        StudentGuardian.objects.create(student=cls.student_other, parent=cls.parent_other, relationship='mother')

        cls.assignment = TeacherAssignment.objects.create(
            teacher=cls.teacher, school=cls.school_a, academic_year=cls.year_a,
            classroom=cls.class_a, section=cls.section_a, subject=cls.subject_a,
        )
        cls.assignment_other = TeacherAssignment.objects.create(
            teacher=cls.teacher_other, school=cls.school_a, academic_year=cls.year_a,
            classroom=cls.class_other, section=cls.section_other, subject=cls.subject_a,
        )
        cls.assignment_b = TeacherAssignment.objects.create(
            teacher=cls.teacher_b, school=cls.school_b, academic_year=cls.year_b,
            classroom=cls.class_b, section=cls.section_b, subject=cls.subject_b,
        )
        cls.attendance = Attendance.objects.create(
            student_enrollment=cls.enrollment, teacher_assignment=cls.assignment,
            academic_term=cls.term_a, attendance_date=cls.day, status='present',
        )
        cls.attendance_other = Attendance.objects.create(
            student_enrollment=cls.enrollment_other, teacher_assignment=cls.assignment_other,
            academic_term=cls.term_a, attendance_date=cls.day, status='absent',
        )
        cls.attendance_b = Attendance.objects.create(
            student_enrollment=cls.enrollment_b, teacher_assignment=cls.assignment_b,
            academic_term=cls.term_b, attendance_date=cls.day, status='late',
        )

    @classmethod
    def user(cls, username, role, school, year):
        return User.objects.create_user(username=username, password=cls.password, role=role, school=school, academic_year=year)

    @classmethod
    def enroll(cls, student, school, year, classroom, section):
        return StudentEnrollment.objects.create(
            student=student, school=school, academic_year=year, classroom=classroom,
            section=section, status='active', is_current=True,
        )

    def auth(self, user):
        self.client.force_authenticate(user=user)

    def results(self, response):
        return response.data['results']

    def payload(self, enrollment=None, assignment=None, **overrides):
        data = {
            'student_enrollment': (enrollment or self.enrollment_peer).id,
            'teacher_assignment': (assignment or self.assignment).id,
            'academic_term': self.term_a.id,
            'attendance_date': '2026-07-30', 'status': 'present', 'note': '',
        }
        data.update(overrides)
        return data

    def bulk_payload(self, students=None, assignment=None):
        return {
            'teacher_assignment_id': (assignment or self.assignment).id,
            'attendance_date': '2026-07-30', 'academic_term_id': self.term_a.id,
            'students': students or [
                {'student_enrollment_id': self.enrollment.id, 'status': 'present', 'note': ''},
                {'student_enrollment_id': self.enrollment_peer.id, 'status': 'absent', 'note': 'Medical'},
            ],
        }

    def test_01_super_admin_lists_multiple_schools(self):
        self.auth(self.super_admin); response = self.client.get(reverse('attendance-list'), {'page_size': 100})
        self.assertEqual({r['id'] for r in self.results(response)}, {self.attendance.id, self.attendance_other.id, self.attendance_b.id})

    def test_02_school_admin_lists_own_school(self):
        self.auth(self.admin_a); response = self.client.get(reverse('attendance-list'), {'page_size': 100})
        self.assertEqual({r['id'] for r in self.results(response)}, {self.attendance.id, self.attendance_other.id})

    def test_03_teacher_lists_own_assignments(self):
        self.auth(self.teacher_user); response = self.client.get(reverse('attendance-list'), {'page_size': 100})
        self.assertEqual([r['id'] for r in self.results(response)], [self.attendance.id])

    def test_04_parent_lists_children(self):
        self.auth(self.parent_user); response = self.client.get(reverse('attendance-list'))
        self.assertEqual([r['id'] for r in self.results(response)], [self.attendance.id])

    def test_05_student_lists_self(self):
        self.auth(self.student_user); response = self.client.get(reverse('attendance-list'))
        self.assertEqual([r['id'] for r in self.results(response)], [self.attendance.id])

    def test_06_unauthenticated_is_401(self):
        self.assertEqual(self.client.get(reverse('attendance-list')).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_07_disabled_school_is_403(self):
        School.objects.filter(pk=self.school_a.pk).update(is_active=False); self.admin_a.refresh_from_db(); self.auth(self.admin_a)
        self.assertEqual(self.client.get(reverse('attendance-list')).status_code, status.HTTP_403_FORBIDDEN)

    def test_08_admin_cannot_detail_other_school(self):
        self.auth(self.admin_a); self.assertEqual(self.client.get(reverse('attendance-detail', args=[self.attendance_b.id])).status_code, 404)

    def test_09_teacher_cannot_detail_other_assignment(self):
        self.auth(self.teacher_user); self.assertEqual(self.client.get(reverse('attendance-detail', args=[self.attendance_other.id])).status_code, 404)

    def test_10_parent_cannot_detail_other_child(self):
        self.auth(self.parent_user); self.assertEqual(self.client.get(reverse('attendance-detail', args=[self.attendance_other.id])).status_code, 404)

    def test_11_student_cannot_detail_other_student(self):
        self.auth(self.student_user); self.assertEqual(self.client.get(reverse('attendance-detail', args=[self.attendance_other.id])).status_code, 404)

    def test_12_out_of_scope_404_is_formatted(self):
        self.auth(self.admin_a); response = self.client.get(reverse('attendance-detail', args=[self.attendance_b.id]))
        self.assertEqual(response.data, {'success': False, 'message': 'Not found.', 'errors': {}})

    def test_13_admin_creates_inside_school(self):
        self.auth(self.admin_a); self.assertEqual(self.client.post(reverse('attendance-list'), self.payload()).status_code, 201)

    def test_14_teacher_creates_inside_assignment(self):
        self.auth(self.teacher_user); self.assertEqual(self.client.post(reverse('attendance-list'), self.payload()).status_code, 201)

    def test_15_teacher_cannot_create_outside_assignment(self):
        self.auth(self.teacher_user); response = self.client.post(reverse('attendance-list'), self.payload(self.enrollment_other, self.assignment_other))
        self.assertEqual(response.status_code, 400)

    def test_16_parent_cannot_create(self):
        self.auth(self.parent_user); self.assertEqual(self.client.post(reverse('attendance-list'), self.payload()).status_code, 403)

    def test_17_student_cannot_create(self):
        self.auth(self.student_user); self.assertEqual(self.client.post(reverse('attendance-list'), self.payload()).status_code, 403)

    def test_18_update_inside_scope(self):
        self.auth(self.admin_a); response = self.client.patch(reverse('attendance-detail', args=[self.attendance.id]), {'status': 'late'})
        self.assertEqual(response.status_code, 200); self.assertEqual(response.data['status'], 'late')

    def test_19_update_outside_scope_is_404(self):
        self.auth(self.admin_a); self.assertEqual(self.client.patch(reverse('attendance-detail', args=[self.attendance_b.id]), {'status': 'present'}).status_code, 404)

    def test_20_mismatched_relationships_rejected(self):
        self.auth(self.admin_a); response = self.client.post(reverse('attendance-list'), self.payload(self.enrollment_other, self.assignment))
        self.assertEqual(response.status_code, 400)

    def test_21_single_duplicate_rejected(self):
        self.auth(self.admin_a); response = self.client.post(reverse('attendance-list'), self.payload(self.enrollment, self.assignment, attendance_date='2026-07-29'))
        self.assertEqual(response.status_code, 400)

    def test_22_bulk_success(self):
        self.auth(self.admin_a); response = self.client.post(reverse('attendance-bulk'), self.bulk_payload(), format='json')
        self.assertEqual(response.status_code, 200); self.assertTrue(response.data['success'])

    def test_23_bulk_creates_multiple(self):
        self.auth(self.admin_a); response = self.client.post(reverse('attendance-bulk'), self.bulk_payload(), format='json')
        self.assertEqual(response.data['created'], 2); self.assertEqual(response.data['total'], 2)

    def test_24_bulk_updates_existing(self):
        Attendance.objects.create(student_enrollment=self.enrollment, teacher_assignment=self.assignment, academic_term=self.term_a, attendance_date=date(2026, 7, 30), status='absent')
        self.auth(self.admin_a); response = self.client.post(reverse('attendance-bulk'), self.bulk_payload(), format='json')
        self.assertEqual(response.data['updated'], 1); self.assertEqual(response.data['created'], 1)

    def test_25_bulk_rejects_duplicate_ids(self):
        students = [{'student_enrollment_id': self.enrollment.id, 'status': 'present'}, {'student_enrollment_id': self.enrollment.id, 'status': 'absent'}]
        self.auth(self.admin_a); self.assertEqual(self.client.post(reverse('attendance-bulk'), self.bulk_payload(students), format='json').status_code, 400)

    def test_26_bulk_rejects_one_outside_class(self):
        students = [{'student_enrollment_id': self.enrollment.id, 'status': 'present'}, {'student_enrollment_id': self.enrollment_other.id, 'status': 'absent'}]
        self.auth(self.admin_a); self.assertEqual(self.client.post(reverse('attendance-bulk'), self.bulk_payload(students), format='json').status_code, 400)

    def test_27_bulk_has_no_partial_save(self):
        students = [{'student_enrollment_id': self.enrollment.id, 'status': 'present'}, {'student_enrollment_id': self.enrollment_other.id, 'status': 'absent'}]
        self.auth(self.admin_a); self.client.post(reverse('attendance-bulk'), self.bulk_payload(students), format='json')
        self.assertFalse(Attendance.objects.filter(student_enrollment=self.enrollment, attendance_date=date(2026, 7, 30)).exists())

    def test_28_teacher_cannot_bulk_other_assignment(self):
        self.auth(self.teacher_user); response = self.client.post(reverse('attendance-bulk'), self.bulk_payload(assignment=self.assignment_other), format='json')
        self.assertEqual(response.status_code, 400)

    def test_29_parent_and_student_cannot_bulk(self):
        for user in (self.parent_user, self.student_user):
            client = APIClient(); client.force_authenticate(user=user)
            self.assertEqual(client.post(reverse('attendance-bulk'), self.bulk_payload(), format='json').status_code, 403)

    def test_30_daily_totals(self):
        self.auth(self.admin_a); response = self.client.get(reverse('attendance-daily'), {'date': '2026-07-29'})
        self.assertEqual(response.data['recorded'], 2); self.assertEqual(response.data['present'], 1); self.assertEqual(response.data['absent'], 1)

    def test_31_daily_not_recorded(self):
        self.auth(self.admin_a); response = self.client.get(reverse('attendance-daily'), {'date': '2026-07-29', 'teacher_assignment_id': self.assignment.id})
        self.assertEqual(response.data['total_students'], 2); self.assertEqual(response.data['not_recorded'], 1)

    def test_32_teacher_daily_is_scoped(self):
        self.auth(self.teacher_user); response = self.client.get(reverse('attendance-daily'), {'date': '2026-07-29'})
        self.assertEqual(response.data['recorded'], 1); self.assertEqual(len(response.data['records']), 1)

    def test_33_student_summary_percentage(self):
        Attendance.objects.create(student_enrollment=self.enrollment, teacher_assignment=self.assignment, academic_term=self.term_a, attendance_date=date(2026, 7, 30), status='late')
        self.auth(self.student_user); response = self.client.get(reverse('attendance-student-summary', args=[self.student.id]))
        self.assertEqual(response.data['attendance_percentage'], 100.0)

    def test_34_parent_can_summary_child(self):
        self.auth(self.parent_user); self.assertEqual(self.client.get(reverse('attendance-student-summary', args=[self.student.id])).status_code, 200)

    def test_35_parent_cannot_summary_other_child(self):
        self.auth(self.parent_user); self.assertEqual(self.client.get(reverse('attendance-student-summary', args=[self.student_other.id])).status_code, 404)

    def test_36_class_summary_totals(self):
        self.auth(self.admin_a); response = self.client.get(reverse('attendance-class-summary', args=[self.class_a.id]), {'section_id': self.section_a.id})
        self.assertEqual(response.data['total_students'], 2); self.assertEqual(response.data['total_attendance_records'], 1)

    def test_37_teacher_cannot_summary_other_class(self):
        self.auth(self.teacher_user); self.assertEqual(self.client.get(reverse('attendance-class-summary', args=[self.class_other.id])).status_code, 404)

    def test_38_date_filters_work(self):
        self.auth(self.admin_a); response = self.client.get(reverse('attendance-student-summary', args=[self.student.id]), {'date_from': '2026-07-30'})
        self.assertEqual(response.data['total_records'], 0)

    def test_39_status_filter_works(self):
        self.auth(self.admin_a); response = self.client.get(reverse('attendance-list'), {'status': 'absent', 'page_size': 100})
        self.assertEqual([item['id'] for item in self.results(response)], [self.attendance_other.id])

    def test_40_old_access_disabled_school_is_403(self):
        login = self.client.post(reverse('token_obtain_pair'), {'username': self.admin_a.username, 'password': self.password})
        School.objects.filter(pk=self.school_a.pk).update(is_active=False)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        self.assertEqual(self.client.get(reverse('attendance-list')).status_code, 403)

    def test_41_direct_other_school_id_hides_record(self):
        self.auth(self.admin_a); response = self.client.get(reverse('attendance-detail', args=[self.attendance_b.id]))
        self.assertEqual(response.status_code, 404); self.assertNotIn('Student B', str(response.data))

    def test_42_validation_error_is_formatted(self):
        self.auth(self.admin_a); response = self.client.post(reverse('attendance-list'), {})
        self.assertEqual(response.status_code, 400); self.assertFalse(response.data['success']); self.assertEqual(response.data['message'], 'Validation failed.')
    def test_43_daily_status_filter_does_not_change_summary(self):
        self.auth(self.admin_a)
        response = self.client.get(reverse('attendance-daily'), {
            'date': '2026-07-29', 'status': 'absent',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['recorded'], 2)
        self.assertEqual(response.data['not_recorded'], 1)
        self.assertEqual(response.data['present'], 1)
        self.assertEqual(response.data['absent'], 1)
        self.assertEqual(response.data['records_filter'], {'status': 'absent'})
        self.assertEqual(len(response.data['records']), 1)

    def test_44_admin_daily_counts_class_without_assignment(self):
        classroom = Classroom.objects.create(
            school=self.school_a, academic_year=self.year_a,
            name='No Assignment', code='NA',
        )
        section = Section.objects.create(
            school=self.school_a, academic_year=self.year_a,
            classroom=classroom, name='NA', code='NA',
        )
        student = Student.objects.create(
            school=self.school_a, full_name='Unassigned Student',
            student_code='ATA-S90001', gender='male',
        )
        self.enroll(student, self.school_a, self.year_a, classroom, section)
        self.auth(self.admin_a)
        response = self.client.get(reverse('attendance-daily'), {
            'date': '2026-07-29', 'classroom_id': classroom.id,
            'section_id': section.id,
        })
        self.assertEqual(response.data['total_students'], 1)
        self.assertEqual(response.data['recorded'], 0)
        self.assertEqual(response.data['not_recorded'], 1)

    def test_45_teacher_daily_remains_current_assignment_scoped(self):
        TeacherAssignment.objects.filter(pk=self.assignment_other.pk).update(
            teacher=self.teacher,
        )
        TeacherAssignment.objects.filter(pk=self.assignment_other.pk).update(
            is_current=False,
        )
        self.auth(self.teacher_user)
        response = self.client.get(reverse('attendance-daily'), {
            'date': '2026-07-29',
        })
        self.assertEqual(response.data['recorded'], 1)
        self.assertEqual(
            [item['id'] for item in response.data['records']],
            [self.attendance.id],
        )

    def test_46_teacher_cannot_create_with_non_current_assignment(self):
        TeacherAssignment.objects.filter(pk=self.assignment.pk).update(is_current=False)
        self.assignment.refresh_from_db()
        self.auth(self.teacher_user)
        response = self.client.post(reverse('attendance-list'), self.payload())
        self.assertEqual(response.status_code, 400)

    def test_47_teacher_cannot_use_assignment_from_different_user_year(self):
        other_year = AcademicYear.objects.create(
            school=self.school_a, name='2027 A',
            start_date=date(2027, 1, 1), end_date=date(2027, 12, 31),
        )
        User.objects.filter(pk=self.teacher_user.pk).update(academic_year=other_year)
        self.teacher_user.refresh_from_db()
        self.auth(self.teacher_user)
        response = self.client.post(reverse('attendance-list'), self.payload())
        self.assertEqual(response.status_code, 400)

    def test_48_teacher_cannot_create_outside_assignment_period(self):
        TeacherAssignment.objects.filter(pk=self.assignment.pk).update(
            start_date=date(2026, 7, 31),
        )
        self.assignment.refresh_from_db()
        self.auth(self.teacher_user)
        response = self.client.post(reverse('attendance-list'), self.payload())
        self.assertEqual(response.status_code, 400)

    def test_49_admin_can_manage_historical_assignment(self):
        TeacherAssignment.objects.filter(pk=self.assignment.pk).update(
            is_current=False, start_date=date(2026, 8, 1),
        )
        self.assignment.refresh_from_db()
        self.auth(self.admin_a)
        response = self.client.post(reverse('attendance-list'), self.payload())
        self.assertEqual(response.status_code, 201)

    def test_50_create_rejects_inactive_enrollment(self):
        StudentEnrollment.objects.filter(pk=self.enrollment_peer.pk).update(
            status='transferred',
        )
        self.enrollment_peer.refresh_from_db()
        self.auth(self.admin_a)
        self.assertEqual(
            self.client.post(reverse('attendance-list'), self.payload()).status_code,
            400,
        )

    def test_51_create_rejects_non_current_enrollment(self):
        StudentEnrollment.objects.filter(pk=self.enrollment_peer.pk).update(
            is_current=False,
        )
        self.enrollment_peer.refresh_from_db()
        self.auth(self.admin_a)
        self.assertEqual(
            self.client.post(reverse('attendance-list'), self.payload()).status_code,
            400,
        )

    def test_52_admin_can_edit_status_on_historical_record(self):
        StudentEnrollment.objects.filter(pk=self.enrollment.pk).update(
            status='transferred', is_current=False,
        )
        self.enrollment.refresh_from_db()
        self.auth(self.admin_a)
        response = self.client.patch(
            reverse('attendance-detail', args=[self.attendance.id]),
            {'status': 'excused', 'note': 'Historical correction'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'excused')

    def test_53_moving_record_to_historical_enrollment_is_rejected(self):
        StudentEnrollment.objects.filter(pk=self.enrollment_peer.pk).update(
            is_current=False,
        )
        self.enrollment_peer.refresh_from_db()
        self.auth(self.admin_a)
        response = self.client.patch(
            reverse('attendance-detail', args=[self.attendance.id]),
            {'student_enrollment': self.enrollment_peer.id},
        )
        self.assertEqual(response.status_code, 400)

    def test_54_valid_section_class_summary_works(self):
        self.auth(self.admin_a)
        response = self.client.get(
            reverse('attendance-class-summary', args=[self.class_a.id]),
            {'section_id': self.section_a.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['section'], self.section_a.id)

    def test_55_section_from_another_class_returns_404(self):
        self.auth(self.admin_a)
        response = self.client.get(
            reverse('attendance-class-summary', args=[self.class_a.id]),
            {'section_id': self.section_other.id},
        )
        self.assertEqual(response.status_code, 404)

    def test_56_section_from_another_school_returns_404(self):
        self.auth(self.admin_a)
        response = self.client.get(
            reverse('attendance-class-summary', args=[self.class_a.id]),
            {'section_id': self.section_b.id},
        )
        self.assertEqual(response.status_code, 404)

    def test_57_teacher_cannot_request_section_outside_assignment(self):
        self.auth(self.teacher_user)
        response = self.client.get(
            reverse('attendance-class-summary', args=[self.class_other.id]),
            {'section_id': self.section_other.id},
        )
        self.assertEqual(response.status_code, 404)

    def test_58_duplicate_conflict_detection_is_constraint_specific(self):
        from .services.attendance import _is_attendance_duplicate_conflict

        class DatabaseCause(Exception):
            pass

        duplicate = IntegrityError('duplicate')
        duplicate_cause = DatabaseCause('database duplicate')
        duplicate_cause.diag = type('Diagnostics', (), {
            'constraint_name': 'unique_student_attendance_per_day',
        })()
        duplicate.__cause__ = duplicate_cause
        other = IntegrityError('other')
        other_cause = DatabaseCause('other database error')
        other_cause.diag = type('Diagnostics', (), {
            'constraint_name': 'some_other_constraint',
        })()
        other.__cause__ = other_cause
        self.assertTrue(_is_attendance_duplicate_conflict(duplicate))
        self.assertFalse(_is_attendance_duplicate_conflict(other))
