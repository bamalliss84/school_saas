from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import (
    AcademicYear, ClassSubject, Classroom, School, SchoolMembership,
    SchoolPeriod, Section, Student, StudentEnrollment, Subject, Teacher,
    TeacherAssignment, TimetableEntry,
)

User = get_user_model()


class AcademicStructureAndTeacherManagementTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # School A
        self.school_a = School.objects.create(name='School A', code='SCH_A', is_active=True)
        self.year_a = AcademicYear.objects.create(
            school=self.school_a, name='2026-2027',
            start_date='2026-09-01', end_date='2027-06-30', is_active=True,
        )

        # School B (for isolation tests)
        self.school_b = School.objects.create(name='School B', code='SCH_B', is_active=True)
        self.year_b = AcademicYear.objects.create(
            school=self.school_b, name='2026-2027',
            start_date='2026-09-01', end_date='2027-06-30', is_active=True,
        )

        # Admin Users
        self.admin_a = User.objects.create_user(
            username='admin_a', password='password123', role='school_admin',
            school=self.school_a, is_active_school_user=True,
        )
        self.membership_admin_a = SchoolMembership.objects.create(
            user=self.admin_a, school=self.school_a, role='school_admin',
            status='active', is_default=True,
        )

        self.admin_b = User.objects.create_user(
            username='admin_b', password='password123', role='school_admin',
            school=self.school_b, is_active_school_user=True,
        )
        self.membership_admin_b = SchoolMembership.objects.create(
            user=self.admin_b, school=self.school_b, role='school_admin',
            status='active', is_default=True,
        )

        # Historical Admin User in School A
        self.admin_hist = User.objects.create_user(
            username='admin_hist', password='password123', role='school_admin',
            school=self.school_a, is_active_school_user=True,
        )
        self.membership_admin_hist = SchoolMembership.objects.create(
            user=self.admin_hist, school=self.school_a, role='school_admin',
            status='historical', is_default=False,
        )

        # Teacher User in School A
        self.teacher_user = User.objects.create_user(
            username='teacher_a', password='password123', role='teacher',
            school=self.school_a, is_active_school_user=True,
        )
        self.membership_teacher_a = SchoolMembership.objects.create(
            user=self.teacher_user, school=self.school_a, role='teacher',
            status='active', is_default=True,
        )

    def login_user(self, username, membership):
        res = self.client.post('/api/v1/auth/login/', {'username': username, 'password': 'password123'})
        self.assertEqual(res.status_code, 200, res.data)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {res.data['access']}",
            HTTP_X_SCHOOL_MEMBERSHIP_ID=str(membership.pk),
        )

    # -------------------------------------------------------------
    # CLASSROOM TESTS
    # -------------------------------------------------------------
    def test_classroom_crud_and_scoping(self):
        self.login_user('admin_a', self.membership_admin_a)

        # 1. Create Classroom in School A
        res = self.client.post('/api/v1/classes/', {
            'name': 'Grade 10',
            'code': 'G10',
            'is_active': True,
        })
        self.assertEqual(res.status_code, 201, res.data)
        class_id = res.data['id']
        self.assertEqual(res.data['name'], 'Grade 10')
        self.assertEqual(res.data['code'], 'G10')
        self.assertEqual(res.data['school']['id'], self.school_a.id)
        self.assertEqual(res.data['academic_year'], self.year_a.id)

        # 2. Duplicate code in same academic year rejected
        dup = self.client.post('/api/v1/classes/', {
            'name': 'Grade 10 Duplicate',
            'code': 'G10',
        })
        self.assertEqual(dup.status_code, 400)
        self.assertIn('code', dup.data.get('errors', dup.data))

        # 3. List classrooms scoped to School A
        list_res = self.client.get('/api/v1/classes/')
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(list_res.data['count'], 1)
        self.assertEqual(list_res.data['results'][0]['id'], class_id)

        # 4. Retrieve Detail
        detail = self.client.get(f'/api/v1/classes/{class_id}/')
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data['name'], 'Grade 10')

        # 5. Update Classroom
        update_res = self.client.patch(f'/api/v1/classes/{class_id}/', {
            'name': 'Grade 10 - Advanced',
        })
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.data['name'], 'Grade 10 - Advanced')

        # 6. Delete Classroom
        del_res = self.client.delete(f'/api/v1/classes/{class_id}/')
        self.assertEqual(del_res.status_code, 204)
        self.assertFalse(Classroom.objects.filter(pk=class_id).exists())

    def test_classroom_cross_school_isolation(self):
        # Create classroom in School B
        class_b = Classroom.objects.create(
            school=self.school_b, academic_year=self.year_b, name='Grade 11', code='G11',
        )

        # Login as Admin A
        self.login_user('admin_a', self.membership_admin_a)

        # Attempt to get School B classroom -> 404
        self.assertEqual(self.client.get(f'/api/v1/classes/{class_b.pk}/').status_code, 404)

        # Attempt to update School B classroom -> 404
        self.assertEqual(self.client.patch(f'/api/v1/classes/{class_b.pk}/', {'name': 'Hacked'}).status_code, 404)

        # Attempt to delete School B classroom -> 404
        self.assertEqual(self.client.delete(f'/api/v1/classes/{class_b.pk}/').status_code, 404)

    def test_classroom_historical_and_role_protection(self):
        class_a = Classroom.objects.create(
            school=self.school_a, academic_year=self.year_a, name='Grade 9', code='G9',
        )

        # Historical Admin -> Read allowed, Write rejected (403)
        self.login_user('admin_hist', self.membership_admin_hist)
        self.assertEqual(self.client.get(f'/api/v1/classes/{class_a.pk}/').status_code, 200)
        self.assertEqual(self.client.post('/api/v1/classes/', {'name': 'Grade 8', 'code': 'G8'}).status_code, 403)
        self.assertEqual(self.client.patch(f'/api/v1/classes/{class_a.pk}/', {'name': 'New'}).status_code, 403)
        self.assertEqual(self.client.delete(f'/api/v1/classes/{class_a.pk}/').status_code, 403)

        # Teacher user -> Read/Write rejected (403)
        self.login_user('teacher_a', self.membership_teacher_a)
        self.assertEqual(self.client.get('/api/v1/classes/').status_code, 403)
        self.assertEqual(self.client.post('/api/v1/classes/', {'name': 'Grade 8', 'code': 'G8'}).status_code, 403)

    # -------------------------------------------------------------
    # SECTION TESTS
    # -------------------------------------------------------------
    def test_section_crud_and_cross_school_validation(self):
        class_a = Classroom.objects.create(
            school=self.school_a, academic_year=self.year_a, name='Grade 10', code='G10',
        )
        class_b = Classroom.objects.create(
            school=self.school_b, academic_year=self.year_b, name='Grade 10 B', code='G10B',
        )

        self.login_user('admin_a', self.membership_admin_a)

        # 1. Reject section creation with foreign classroom
        foreign = self.client.post('/api/v1/sections/', {
            'classroom': class_b.pk,
            'name': 'Section A',
            'code': 'SEC-A',
        })
        self.assertEqual(foreign.status_code, 400)
        self.assertIn('classroom', foreign.data.get('errors', foreign.data))

        # 2. Create section in valid classroom
        res = self.client.post('/api/v1/sections/', {
            'classroom': class_a.pk,
            'name': 'Section A',
            'code': 'SEC-A',
        })
        self.assertEqual(res.status_code, 201, res.data)
        sec_id = res.data['id']
        self.assertEqual(res.data['classroom'], class_a.pk)
        self.assertEqual(res.data['academic_year'], self.year_a.pk)

        # 3. Duplicate section code in same classroom rejected
        dup = self.client.post('/api/v1/sections/', {
            'classroom': class_a.pk,
            'name': 'Section A Duplicate',
            'code': 'SEC-A',
        })
        self.assertEqual(dup.status_code, 400)

        # 4. List sections filtered by classroom
        list_res = self.client.get('/api/v1/sections/', {'classroom_id': class_a.pk})
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(list_res.data['count'], 1)

        # 5. Delete section
        del_res = self.client.delete(f'/api/v1/sections/{sec_id}/')
        self.assertEqual(del_res.status_code, 204)
        self.assertFalse(Section.objects.filter(pk=sec_id).exists())

    # -------------------------------------------------------------
    # SUBJECT & CLASS-SUBJECT TESTS
    # -------------------------------------------------------------
    def test_subject_and_class_subject_management(self):
        class_a = Classroom.objects.create(
            school=self.school_a, academic_year=self.year_a, name='Grade 10', code='G10',
        )
        self.login_user('admin_a', self.membership_admin_a)

        # 1. Create Subject
        subj_res = self.client.post('/api/v1/subjects/', {
            'name': 'Mathematics',
            'code': 'MATH-10',
        })
        self.assertEqual(subj_res.status_code, 201, subj_res.data)
        subj_id = subj_res.data['id']

        # 2. Duplicate subject code rejected
        dup_subj = self.client.post('/api/v1/subjects/', {
            'name': 'Math 2',
            'code': 'MATH-10',
        })
        self.assertEqual(dup_subj.status_code, 400)

        # 3. Link Subject to Classroom (ClassSubject)
        cs_res = self.client.post('/api/v1/class-subjects/', {
            'classroom': class_a.pk,
            'subject': subj_id,
            'weekly_periods': 5,
        })
        self.assertEqual(cs_res.status_code, 201, cs_res.data)
        cs_id = cs_res.data['id']
        self.assertEqual(cs_res.data['weekly_periods'], 5)

        # 4. Duplicate ClassSubject rejected
        dup_cs = self.client.post('/api/v1/class-subjects/', {
            'classroom': class_a.pk,
            'subject': subj_id,
            'weekly_periods': 3,
        })
        self.assertEqual(dup_cs.status_code, 400)

        # 5. Delete subject rejected while linked to classroom
        del_subj_blocked = self.client.delete(f'/api/v1/subjects/{subj_id}/')
        self.assertEqual(del_subj_blocked.status_code, 400)

        # 6. Delete class subject link, then delete subject
        self.assertEqual(self.client.delete(f'/api/v1/class-subjects/{cs_id}/').status_code, 204)
        self.assertEqual(self.client.delete(f'/api/v1/subjects/{subj_id}/').status_code, 204)

    # -------------------------------------------------------------
    # TEACHER & TEACHER ASSIGNMENT TESTS
    # -------------------------------------------------------------
    def test_teacher_crud_and_account_creation(self):
        self.login_user('admin_a', self.membership_admin_a)

        # 1. Create Teacher with user login credentials
        res = self.client.post('/api/v1/teachers/', {
            'full_name': 'Prof. Tariq Mansour',
            'specialization': 'Physics',
            'phone': '0501234567',
            'email': 'tariq@school.com',
            'account_username': 'tariq_m',
            'account_password': 'TeacherPass123!',
        })
        self.assertEqual(res.status_code, 201, res.data)
        teacher_id = res.data['id']
        self.assertEqual(res.data['full_name'], 'Prof. Tariq Mansour')
        self.assertTrue(res.data['employee_code'].startswith('SCH_A-T'))
        self.assertEqual(res.data['username'], 'tariq_m')

        # Verify User and SchoolMembership were created
        teacher_obj = Teacher.objects.get(pk=teacher_id)
        self.assertIsNotNone(teacher_obj.user)
        self.assertTrue(SchoolMembership.objects.filter(
            user=teacher_obj.user, school=self.school_a, role='teacher', status='active',
        ).exists())

        # 2. List teachers
        list_res = self.client.get('/api/v1/teachers/', {'search': 'Tariq'})
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(list_res.data['count'], 1)

        # 3. Update teacher specialization
        patch_res = self.client.patch(f'/api/v1/teachers/{teacher_id}/', {
            'specialization': 'Advanced Physics',
        })
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.data['specialization'], 'Advanced Physics')

    def test_teacher_assignment_crud_and_validations(self):
        class_a = Classroom.objects.create(
            school=self.school_a, academic_year=self.year_a, name='Grade 10', code='G10',
        )
        sec_a = Section.objects.create(
            school=self.school_a, academic_year=self.year_a, classroom=class_a, name='A', code='A',
        )
        subj_a = Subject.objects.create(
            school=self.school_a, name='Physics', code='PHYS',
        )
        teacher_a = Teacher.objects.create(
            school=self.school_a, academic_year=self.year_a, full_name='Tariq M',
            user=self.teacher_user,
        )

        # Foreign objects from School B
        class_b = Classroom.objects.create(
            school=self.school_b, academic_year=self.year_b, name='Grade 10 B', code='G10B',
        )
        sec_b = Section.objects.create(
            school=self.school_b, academic_year=self.year_b, classroom=class_b, name='B', code='B',
        )

        self.login_user('admin_a', self.membership_admin_a)

        # 1. Reject assignment with foreign classroom/section
        foreign_res = self.client.post('/api/v1/teacher-assignments/', {
            'teacher': teacher_a.pk,
            'classroom': class_b.pk,
            'section': sec_b.pk,
            'subject': subj_a.pk,
        })
        self.assertEqual(foreign_res.status_code, 400)

        # 2. Create valid teacher assignment
        assign_res = self.client.post('/api/v1/teacher-assignments/', {
            'teacher': teacher_a.pk,
            'classroom': class_a.pk,
            'section': sec_a.pk,
            'subject': subj_a.pk,
            'is_current': True,
        })
        self.assertEqual(assign_res.status_code, 201, assign_res.data)
        assign_id = assign_res.data['id']
        self.assertEqual(assign_res.data['teacher'], teacher_a.pk)
        self.assertEqual(assign_res.data['classroom'], class_a.pk)
        self.assertEqual(assign_res.data['section'], sec_a.pk)
        self.assertEqual(assign_res.data['subject'], subj_a.pk)

        # 3. Duplicate assignment rejected
        dup_assign = self.client.post('/api/v1/teacher-assignments/', {
            'teacher': teacher_a.pk,
            'classroom': class_a.pk,
            'section': sec_a.pk,
            'subject': subj_a.pk,
        })
        self.assertEqual(dup_assign.status_code, 400)

        # 4. List assignments scoped to School A
        list_res = self.client.get('/api/v1/teacher-assignments/', {'teacher_id': teacher_a.pk})
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(list_res.data['count'], 1)

        # 5. Update assignment status
        patch_res = self.client.patch(f'/api/v1/teacher-assignments/{assign_id}/', {
            'is_current': False,
        })
        self.assertEqual(patch_res.status_code, 200)
        self.assertFalse(patch_res.data['is_current'])

        # 6. Delete assignment
        del_res = self.client.delete(f'/api/v1/teacher-assignments/{assign_id}/')
        self.assertEqual(del_res.status_code, 204)
        self.assertFalse(TeacherAssignment.objects.filter(pk=assign_id).exists())

    def test_protected_delete_validations(self):
        self.login_user('admin_a', self.membership_admin_a)

        # Setup structure
        classroom = Classroom.objects.create(
            school=self.school_a, academic_year=self.year_a, name='Grade 12', code='G12',
        )
        section = Section.objects.create(
            school=self.school_a, academic_year=self.year_a, classroom=classroom, name='Section 12-A', code='12A',
        )
        subject = Subject.objects.create(
            school=self.school_a, name='Chemistry', code='CHEM',
        )
        teacher = Teacher.objects.create(
            school=self.school_a, academic_year=self.year_a, full_name='Dr. Omar',
            user=self.teacher_user,
        )
        assignment = TeacherAssignment.objects.create(
            school=self.school_a, academic_year=self.year_a, teacher=teacher,
            classroom=classroom, section=section, subject=subject, is_current=True,
        )

        # 1. Attempt delete classroom while section and assignment exist -> 400
        res_class_del = self.client.delete(f'/api/v1/classes/{classroom.pk}/')
        self.assertEqual(res_class_del.status_code, 400)

        # 2. Add student enrollment to section and attempt section delete -> 400
        student = Student.objects.create(
            school=self.school_a, full_name='Ahmed Ali', student_code='STU-001',
        )
        StudentEnrollment.objects.create(
            student=student, school=self.school_a, academic_year=self.year_a,
            classroom=classroom, section=section, status='active', is_current=True,
        )
        res_sec_del = self.client.delete(f'/api/v1/sections/{section.pk}/')
        self.assertEqual(res_sec_del.status_code, 400)

        # 3. Attempt teacher delete while assignment exists -> 400
        res_teach_del = self.client.delete(f'/api/v1/teachers/{teacher.pk}/')
        self.assertEqual(res_teach_del.status_code, 400)

        # 4. Create period and timetable entry, attempt assignment delete -> 400
        period = SchoolPeriod.objects.create(
            school=self.school_a, academic_year=self.year_a, name='Period 1', sequence=1,
            start_time='08:00:00', end_time='08:45:00', kind='lesson',
        )
        TimetableEntry.objects.create(
            school=self.school_a, academic_year=self.year_a,
            teacher_assignment=assignment, period=period, weekday=0,
        )
        res_assign_del = self.client.delete(f'/api/v1/teacher-assignments/{assignment.pk}/')
        self.assertEqual(res_assign_del.status_code, 400)

    def test_academic_filters_and_search(self):
        self.login_user('admin_a', self.membership_admin_a)

        c1 = Classroom.objects.create(
            school=self.school_a, academic_year=self.year_a, name='Alpha Grade', code='ALPHA', is_active=True,
        )
        c2 = Classroom.objects.create(
            school=self.school_a, academic_year=self.year_a, name='Beta Grade', code='BETA', is_active=False,
        )

        # Search filter
        search_res = self.client.get('/api/v1/classes/', {'search': 'Alpha'})
        self.assertEqual(search_res.status_code, 200)
        self.assertEqual(search_res.data['count'], 1)
        self.assertEqual(search_res.data['results'][0]['id'], c1.pk)

        # Active filter
        active_res = self.client.get('/api/v1/classes/', {'is_active': 'false'})
        self.assertEqual(active_res.status_code, 200)
        self.assertEqual(active_res.data['count'], 1)
        self.assertEqual(active_res.data['results'][0]['id'], c2.pk)

    def test_cross_year_detail_and_list_isolation(self):
        # Create a past academic year in School A
        year_a_past = AcademicYear.objects.create(
            school=self.school_a, name='2025-2026',
            start_date='2025-09-01', end_date='2026-06-30', is_active=False,
        )

        # Create past-year entities in School A
        past_class = Classroom.objects.create(
            school=self.school_a, academic_year=year_a_past, name='Past Grade 10', code='PG10',
        )
        past_section = Section.objects.create(
            school=self.school_a, academic_year=year_a_past, classroom=past_class, name='Past Section A', code='PSEC-A',
        )
        past_subject = Subject.objects.create(
            school=self.school_a, name='Biology', code='BIO',
        )
        past_teacher = Teacher.objects.create(
            school=self.school_a, academic_year=year_a_past, full_name='Past Faculty Member',
        )
        past_cs = ClassSubject.objects.create(
            school=self.school_a, academic_year=year_a_past, classroom=past_class, subject=past_subject, weekly_periods=3,
        )
        past_assignment = TeacherAssignment.objects.create(
            school=self.school_a, academic_year=year_a_past, teacher=past_teacher,
            classroom=past_class, section=past_section, subject=past_subject, is_current=False,
        )

        # Login as Admin A in active year 2026-2027
        self.login_user('admin_a', self.membership_admin_a)

        # 1. Classroom: Direct access to past year record is blocked (404)
        self.assertEqual(self.client.get(f'/api/v1/classes/{past_class.pk}/').status_code, 404)
        self.assertEqual(self.client.patch(f'/api/v1/classes/{past_class.pk}/', {'name': 'Hacked'}).status_code, 404)
        self.assertEqual(self.client.delete(f'/api/v1/classes/{past_class.pk}/').status_code, 404)

        # 2. Section: Direct access to past year record is blocked (404)
        self.assertEqual(self.client.get(f'/api/v1/sections/{past_section.pk}/').status_code, 404)
        self.assertEqual(self.client.patch(f'/api/v1/sections/{past_section.pk}/', {'name': 'Hacked'}).status_code, 404)
        self.assertEqual(self.client.delete(f'/api/v1/sections/{past_section.pk}/').status_code, 404)

        # 3. Teacher: Direct access to past year record is blocked (404)
        self.assertEqual(self.client.get(f'/api/v1/teachers/{past_teacher.pk}/').status_code, 404)
        self.assertEqual(self.client.patch(f'/api/v1/teachers/{past_teacher.pk}/', {'full_name': 'Hacked'}).status_code, 404)
        self.assertEqual(self.client.delete(f'/api/v1/teachers/{past_teacher.pk}/').status_code, 404)

        # 4. ClassSubject: Direct access to past year record is blocked (404)
        self.assertEqual(self.client.get(f'/api/v1/class-subjects/{past_cs.pk}/').status_code, 404)
        self.assertEqual(self.client.patch(f'/api/v1/class-subjects/{past_cs.pk}/', {'weekly_periods': 6}).status_code, 404)
        self.assertEqual(self.client.delete(f'/api/v1/class-subjects/{past_cs.pk}/').status_code, 404)

        # 5. TeacherAssignment: Direct access to past year record is blocked (404)
        self.assertEqual(self.client.get(f'/api/v1/teacher-assignments/{past_assignment.pk}/').status_code, 404)
        self.assertEqual(self.client.patch(f'/api/v1/teacher-assignments/{past_assignment.pk}/', {'is_current': True}).status_code, 404)
        self.assertEqual(self.client.delete(f'/api/v1/teacher-assignments/{past_assignment.pk}/').status_code, 404)

        # 6. Subject: Correctly school-scoped (accessible in active context even if created in prior year)
        subj_res = self.client.get(f'/api/v1/subjects/{past_subject.pk}/')
        self.assertEqual(subj_res.status_code, 200)
        self.assertEqual(subj_res.data['name'], 'Biology')

        # 7. List scoping: Past year records are excluded from current year list by default
        self.assertEqual(self.client.get('/api/v1/classes/').data['count'], 0)
        self.assertEqual(self.client.get('/api/v1/sections/').data['count'], 0)
        self.assertEqual(self.client.get('/api/v1/teachers/').data['count'], 0)
        self.assertEqual(self.client.get('/api/v1/class-subjects/').data['count'], 0)
        self.assertEqual(self.client.get('/api/v1/teacher-assignments/').data['count'], 0)
