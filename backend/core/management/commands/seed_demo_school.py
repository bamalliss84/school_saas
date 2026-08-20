from datetime import date, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.models import (
    AcademicTerm, AcademicYear, Announcement, AnnouncementReceipt, Attendance,
    Classroom, ClassSubject, Conversation, ConversationParticipant, Exam, ExamResult, ExamType, Homework,
    HomeworkSubmission, Notification, Parent, School, SchoolMembership,
    SchoolSetting, Section, Student, StudentEnrollment, StudentGuardian,
    Subject, Teacher, TeacherAssignment, User, Message,
    SchoolPeriod, SchoolTimetableConfig, TimetableEntry,
)


DEMO_PASSWORD = 'DemoPass123!'
DEMO_SCHOOL_CODES = ('DEMO_NOOR', 'DEMO_FUTURE')


class Command(BaseCommand):
    help = 'Create deterministic development-only School SaaS demo data.'

    def add_arguments(self, parser):
        parser.add_argument('--reset-demo', action='store_true')
        parser.add_argument(
            '--allow-non-debug', action='store_true',
            help='Explicitly acknowledge seeding a non-DEBUG non-production environment.',
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options['allow_non_debug']:
            raise CommandError(
                'Demo seeding is disabled when DEBUG=False. Use --allow-non-debug only '
                'in an isolated acceptance environment.',
            )
        with transaction.atomic():
            if options['reset_demo']:
                self._reset_demo()
            summary = self._seed()
        self.stdout.write(self.style.SUCCESS(
            'Demo dataset ready: '
            f"{summary['schools']} schools, {summary['students']} students, "
            f"{summary['attendance']} attendance rows, "
            f"{summary['published_results']} published result rows.",
        ))

    def _reset_demo(self):
        TimetableEntry.objects.filter(school__code__in=DEMO_SCHOOL_CODES).delete()
        Announcement.objects.filter(school__code__in=DEMO_SCHOOL_CODES).delete()
        Conversation.objects.filter(school__code__in=DEMO_SCHOOL_CODES).delete()
        ExamResult.objects.filter(exam__school__code__in=DEMO_SCHOOL_CODES).delete()
        School.objects.filter(code__in=DEMO_SCHOOL_CODES).delete()
        User.objects.filter(username__startswith='demo_').delete()

    def _user(self, username, *, role, school=None, year=None, superuser=False):
        defaults = {
            'email': f'{username}@example.com',
            'role': role,
            'school': school,
            'academic_year': year,
            'is_active': True,
            'is_active_school_user': True,
            'is_staff': superuser,
            'is_superuser': superuser,
        }
        user = User.objects.filter(username=username).first()
        if user is None:
            user = User(username=username, password=make_password(DEMO_PASSWORD), **defaults)
        else:
            for field, value in defaults.items():
                setattr(user, field, value)
            user.set_password(DEMO_PASSWORD)
        user.save()
        return user

    def _membership(self, user, school, role, *, status='active', default=False):
        membership, _ = SchoolMembership.objects.update_or_create(
            user=user, school=school, role=role,
            defaults={'status': status, 'is_default': default},
        )
        return membership

    def _school_structure(self, code, name):
        school, _ = School.objects.update_or_create(
            code=code,
            defaults={
                'name': name, 'is_active': True,
                'email': f'{code.lower()}@example.com', 'phone': '0500000000',
                'address': 'DEMO address only',
            },
        )
        SchoolSetting.objects.update_or_create(
            school=school,
            defaults={
                'school_name_ar': name, 'school_name_en': f'{code} Demo School',
                'timezone': 'Asia/Aden', 'language': 'ar',
            },
        )
        years = {}
        for key, year_name, start, end, active in (
            ('previous', 'DEMO 2024/2025', date(2024, 9, 1), date(2025, 6, 30), False),
            ('current', 'DEMO 2025/2026', date(2025, 9, 1), date(2026, 8, 31), True),
        ):
            years[key], _ = AcademicYear.objects.update_or_create(
                school=school, name=year_name,
                defaults={'start_date': start, 'end_date': end, 'is_active': active},
            )
        terms = {}
        for key, year in years.items():
            terms[key], _ = AcademicTerm.objects.update_or_create(
                school=school, academic_year=year, term_type='term_1',
                defaults={
                    'name': f'DEMO Term 1 {key}', 'start_date': year.start_date,
                    'end_date': min(year.end_date, year.start_date + timedelta(days=119)),
                    'is_active': key == 'current',
                },
            )
        current_year = years['current']
        terms['current_2'], _ = AcademicTerm.objects.update_or_create(
            school=school, academic_year=current_year, term_type='term_2',
            defaults={
                'name': 'DEMO Term 2 current',
                'start_date': max(current_year.start_date, date(2026, 1, 1)),
                'end_date': min(current_year.end_date, date(2026, 4, 30)),
                'is_active': False,
            },
        )
        classrooms, sections = {}, {}
        for year_key, year in years.items():
            for grade in (6, 7):
                classroom, _ = Classroom.objects.update_or_create(
                    school=school, academic_year=year, code=f'DEMO_G{grade}',
                    defaults={'name': f'DEMO Grade {grade}', 'is_active': True},
                )
                classrooms[(year_key, grade)] = classroom
                for section_code in ('A', 'B'):
                    section, _ = Section.objects.update_or_create(
                        school=school, academic_year=year, classroom=classroom,
                        code=f'DEMO_{section_code}',
                        defaults={'name': f'DEMO Section {section_code}', 'is_active': True},
                    )
                    sections[(year_key, grade, section_code)] = section
        subjects = {}
        for code_suffix, name_en in (
            ('MATH', 'Mathematics'), ('AR', 'Arabic'),
            ('SCI', 'Science'), ('EN', 'English'),
        ):
            subject, _ = Subject.objects.update_or_create(
                school=school, code=f'DEMO_{code_suffix}',
                defaults={'name': f'DEMO {name_en}', 'is_active': True},
            )
            subjects[code_suffix] = subject
            for (year_key, _grade), classroom in classrooms.items():
                ClassSubject.objects.update_or_create(
                    school=school, academic_year=years[year_key],
                    classroom=classroom, subject=subject,
                    defaults={'weekly_periods': 4},
                )
        for code_suffix, label, maximum, weight in (
            ('QUIZ', 'اختبار قصير', 20, 10),
            ('MONTHLY', 'اختبار شهري', 20, 10),
            ('MID', 'اختبار منتصف الفصل', 50, 25),
            ('TERM', 'اختبار فصلي', 30, 25),
            ('FINAL', 'اختبار نهائي', 100, 30),
        ):
            ExamType.objects.update_or_create(
                school=school, code=f'DEMO_{code_suffix}',
                defaults={
                    'name': f'DEMO {label}', 'max_score': Decimal(maximum),
                    'weight_percentage': Decimal(weight), 'is_active': True,
                },
            )
        return {
            'school': school, 'years': years, 'terms': terms,
            'classrooms': classrooms, 'sections': sections, 'subjects': subjects,
        }

    def _seed(self):
        a = self._school_structure('DEMO_NOOR', 'مدرسة النور التجريبية')
        b = self._school_structure('DEMO_FUTURE', 'مدرسة المستقبل التجريبية')
        school_a, school_b = a['school'], b['school']
        year_a, year_b = a['years']['current'], b['years']['current']

        super_admin = self._user('demo_super_admin', role='super_admin', superuser=True)
        admin_a = self._user('demo_school_a_admin', role='school_admin', school=school_a, year=year_a)
        admin_b = self._user('demo_school_b_admin', role='school_admin', school=school_b, year=year_b)
        teacher_a_user = self._user('demo_teacher_a', role='teacher', school=school_a, year=year_a)
        teacher_b_user = self._user('demo_teacher_b', role='teacher', school=school_b, year=year_b)
        multi_user = self._user('demo_teacher_multi', role='teacher', school=school_a, year=year_a)
        self._membership(admin_a, school_a, 'school_admin', default=True)
        self._membership(admin_b, school_b, 'school_admin', default=True)
        teacher_a_m = self._membership(teacher_a_user, school_a, 'teacher', default=True)
        self._membership(teacher_b_user, school_b, 'teacher', default=True)
        multi_a = self._membership(multi_user, school_a, 'teacher', default=True)
        self._membership(multi_user, school_b, 'teacher')

        teacher_a, _ = Teacher.objects.update_or_create(
            user=teacher_a_user,
            defaults={
                'school': school_a, 'academic_year': year_a, 'full_name': 'DEMO Teacher A',
                'employee_code': 'DEMO_TA',
            },
        )
        teacher_b, _ = Teacher.objects.update_or_create(
            user=teacher_b_user,
            defaults={
                'school': school_b, 'academic_year': year_b, 'full_name': 'DEMO Teacher B',
                'employee_code': 'DEMO_TB',
            },
        )
        teacher_multi, _ = Teacher.objects.update_or_create(
            user=multi_user,
            defaults={
                'school': school_a, 'academic_year': year_a,
                'full_name': 'DEMO Multi School Teacher', 'employee_code': 'DEMO_TM',
            },
        )
        assignment_specs = (
            ('a_math', teacher_a, a, 6, 'A', 'MATH'),
            ('a_arabic_g6', teacher_a, a, 6, 'A', 'AR'),
            ('a_science_g6', teacher_a, a, 6, 'A', 'SCI'),
            ('a_science', teacher_multi, a, 7, 'A', 'SCI'),
            ('b_math', teacher_multi, b, 6, 'B', 'MATH'),
            ('b_english', teacher_b, b, 7, 'A', 'EN'),
        )
        assignments = {}
        for key, teacher, structure, grade, section_code, subject_code in assignment_specs:
            assignments[key], _ = TeacherAssignment.objects.update_or_create(
                teacher=teacher, academic_year=structure['years']['current'],
                classroom=structure['classrooms'][('current', grade)],
                section=structure['sections'][('current', grade, section_code)],
                subject=structure['subjects'][subject_code],
                defaults={'school': structure['school'], 'is_current': True},
            )
        assignments['a_math_previous'], _ = TeacherAssignment.objects.update_or_create(
            teacher=teacher_a, academic_year=a['years']['previous'],
            classroom=a['classrooms'][('previous', 6)],
            section=a['sections'][('previous', 6, 'A')], subject=a['subjects']['MATH'],
            defaults={'school': school_a, 'is_current': True},
        )

        periods = {}
        for label, structure in (('a', a), ('b', b)):
            SchoolTimetableConfig.objects.update_or_create(
                school=structure['school'], academic_year=structure['years']['current'],
                defaults={'working_days': [0, 1, 2, 3, 4]},
            )
            for sequence, name, start, end, kind in (
                (1, 'DEMO First Lesson', time(7, 0), time(7, 45), 'lesson'),
                (2, 'DEMO Second Lesson', time(7, 50), time(8, 35), 'lesson'),
                (3, 'DEMO Break', time(8, 35), time(8, 55), 'break'),
                (4, 'DEMO Third Lesson', time(8, 55), time(9, 40), 'lesson'),
            ):
                periods[(label, sequence)], _ = SchoolPeriod.objects.update_or_create(
                    school=structure['school'], academic_year=structure['years']['current'],
                    sequence=sequence,
                    defaults={
                        'name': name, 'start_time': start, 'end_time': end,
                        'kind': kind, 'is_active': True,
                    },
                )
        SchoolTimetableConfig.objects.update_or_create(
            school=school_a, academic_year=a['years']['previous'],
            defaults={'working_days': [0, 1, 2, 3, 4]},
        )
        historical_period, _ = SchoolPeriod.objects.update_or_create(
            school=school_a, academic_year=a['years']['previous'], sequence=1,
            defaults={
                'name': 'DEMO Historical First Lesson', 'start_time': time(7, 0),
                'end_time': time(7, 45), 'kind': 'lesson', 'is_active': True,
            },
        )
        for key, assignment, period, weekday, room in (
            ('a_math_sun', assignments['a_math'], periods[('a', 1)], 0, 'DEMO Room A1'),
            ('a_science_sun', assignments['a_science'], periods[('a', 2)], 0, 'DEMO Lab A'),
            ('a_science_mon', assignments['a_science'], periods[('a', 1)], 1, 'DEMO Lab A'),
            ('b_math_sun', assignments['b_math'], periods[('b', 1)], 0, 'DEMO Room B1'),
            ('b_english_sun', assignments['b_english'], periods[('b', 2)], 0, 'DEMO Room B2'),
            ('b_math_mon', assignments['b_math'], periods[('b', 2)], 1, 'DEMO Room B1'),
        ):
            TimetableEntry.objects.update_or_create(
                school=assignment.school, academic_year=assignment.academic_year,
                teacher_assignment=assignment, weekday=weekday, period=period,
                valid_from=None, valid_to=None,
                defaults={
                    'room_or_location': room, 'is_active': True,
                    'created_by': admin_a if assignment.school_id == school_a.pk else admin_b,
                },
            )
        TimetableEntry.objects.update_or_create(
            school=school_a, academic_year=a['years']['previous'],
            teacher_assignment=assignments['a_math_previous'], weekday=0,
            period=historical_period, valid_from=None, valid_to=None,
            defaults={
                'room_or_location': 'DEMO Historical Room', 'is_active': True,
                'created_by': admin_a,
            },
        )

        parents = {}
        for username, structure in (('demo_parent_a', a), ('demo_parent_multi', b)):
            user = self._user(
                username, role='parent', school=structure['school'],
                year=structure['years']['current'],
            )
            parents[username], _ = Parent.objects.update_or_create(
                user=user,
                defaults={
                    'school': structure['school'], 'full_name': username.replace('_', ' ').title(),
                    'email': f'{username}@example.com', 'phone': '0500000001',
                },
            )
            self._membership(user, structure['school'], 'parent', default=True)

        enrollments = []
        students = []
        for structure, school_label in ((a, 'a'), (b, 'b')):
            for index in range(1, 11):
                username = f'demo_student_{school_label}_{index:02d}'
                user = self._user(
                    username, role='student', school=structure['school'],
                    year=structure['years']['current'],
                )
                student, _ = Student.objects.update_or_create(
                    user=user,
                    defaults={
                        'school': structure['school'], 'full_name': f'DEMO Student {school_label.upper()} {index:02d}',
                        'gender': 'male' if index % 2 else 'female', 'is_active': True,
                    },
                )
                grade = 6 if index <= 6 else 7
                section_code = 'B' if school_label == 'b' and grade == 6 else 'A'
                enrollment, _ = StudentEnrollment.objects.update_or_create(
                    student=student, academic_year=structure['years']['current'],
                    defaults={
                        'school': structure['school'],
                        'classroom': structure['classrooms'][('current', grade)],
                        'section': structure['sections'][('current', grade, section_code)],
                        'status': 'active', 'is_current': True,
                    },
                )
                self._membership(user, structure['school'], 'student', default=True)
                students.append(student)
                enrollments.append(enrollment)

        transferred_user = self._user(
            'demo_student_transferred', role='student', school=school_b, year=year_b,
        )
        transferred, _ = Student.objects.update_or_create(
            user=transferred_user,
            defaults={'school': school_b, 'full_name': 'DEMO Transferred Student', 'gender': 'female'},
        )
        old_enrollment, _ = StudentEnrollment.objects.update_or_create(
            student=transferred, academic_year=a['years']['previous'],
            defaults={
                'school': school_a, 'classroom': a['classrooms'][('previous', 6)],
                'section': a['sections'][('previous', 6, 'A')],
                'status': 'transferred', 'is_current': False,
            },
        )
        current_enrollment, _ = StudentEnrollment.objects.update_or_create(
            student=transferred, academic_year=year_b,
            defaults={
                'school': school_b, 'classroom': b['classrooms'][('current', 6)],
                'section': b['sections'][('current', 6, 'B')],
                'status': 'active', 'is_current': True,
            },
        )
        transferred_old_m = self._membership(transferred_user, school_a, 'student', status='historical')
        transferred_current_m = self._membership(transferred_user, school_b, 'student', default=True)
        enrollments.extend((old_enrollment, current_enrollment))
        students.append(transferred)

        StudentGuardian.objects.update_or_create(
            parent=parents['demo_parent_a'], student=students[0],
            defaults={'relationship': 'father', 'is_primary': True, 'can_receive_notifications': True},
        )
        StudentGuardian.objects.update_or_create(
            parent=parents['demo_parent_a'], student=students[1],
            defaults={'relationship': 'father', 'can_receive_notifications': True},
        )
        StudentGuardian.objects.update_or_create(
            parent=parents['demo_parent_multi'], student=transferred,
            defaults={'relationship': 'guardian', 'is_primary': True, 'can_receive_notifications': True},
        )
        self._membership(
            parents['demo_parent_multi'].user, school_a, 'parent', status='historical',
        )

        for index, enrollment in enumerate(enrollments):
            structure = a if enrollment.school_id == school_a.pk else b
            term_key = 'previous' if enrollment.academic_year_id == structure['years']['previous'].pk else 'current'
            assignment = None
            if term_key == 'current':
                candidate = assignments['a_math'] if enrollment.school_id == school_a.pk else assignments['b_math']
                if candidate.classroom_id == enrollment.classroom_id and candidate.section_id == enrollment.section_id:
                    assignment = candidate
            Attendance.objects.update_or_create(
                student_enrollment=enrollment,
                attendance_date=structure['terms'][term_key].start_date + timedelta(days=10),
                defaults={
                    'teacher_assignment': assignment, 'academic_term': structure['terms'][term_key],
                    'status': ('present', 'absent', 'late', 'excused')[index % 4],
                    'note': 'DEMO attendance',
                },
            )

        homework, _ = Homework.objects.update_or_create(
            teacher_assignment=assignments['a_math'], title='DEMO Published Mathematics Homework',
            defaults={
                'school': school_a, 'academic_year': year_a, 'academic_term': a['terms']['current'],
                'description': 'DEMO homework', 'submission_type': 'text', 'status': 'published',
                'published_at': timezone.now(), 'due_date': timezone.now() + timedelta(days=7),
                'max_grade': Decimal('10'), 'created_by': teacher_a_user,
            },
        )
        Homework.objects.update_or_create(
            teacher_assignment=assignments['b_math'], title='DEMO School B Mathematics Homework',
            defaults={
                'school': school_b, 'academic_year': year_b, 'academic_term': b['terms']['current'],
                'description': 'DEMO School B homework', 'submission_type': 'text_and_attachment', 'status': 'published',
                'published_at': timezone.now(), 'due_date': timezone.now() + timedelta(days=7),
                'max_grade': Decimal('10'), 'created_by': multi_user,
            },
        )
        # Homework V1 submission-mode acceptance data for demo_student_a_01.
        # update_or_create keeps repeated demo seeding idempotent.
        homework_submission_modes = (
            (
                'DEMO Homework - Notebook Only', 'none',
                'حل التمارين من 1 إلى 5 في دفتر الرياضيات. لا يحتاج هذا الواجب إلى تسليم إلكتروني.',
            ),
            (
                'DEMO Homework - Text Answer', 'text',
                'اكتب في التطبيق شرحاً مختصراً لطريقة حل المسألة.',
            ),
            (
                'DEMO Homework - Attachment Only', 'attachment',
                'حل الواجب في الدفتر ثم ارفع صورة واضحة أو ملف PDF للحل.',
            ),
            (
                'DEMO Homework - Text And Attachment', 'text_and_attachment',
                'اكتب ملخص الحل ثم أرفق صورة أو PDF يوضح خطوات الحل كاملة.',
            ),
        )
        for demo_title, submission_type, description in homework_submission_modes:
            Homework.objects.update_or_create(
                teacher_assignment=assignments['a_math'], title=demo_title,
                defaults={
                    'school': school_a, 'academic_year': year_a,
                    'academic_term': a['terms']['current'],
                    'description': description, 'submission_type': submission_type,
                    'status': 'published', 'published_at': timezone.now(),
                    'due_date': timezone.now() + timedelta(days=10),
                    'max_grade': None if submission_type == 'none' else Decimal('10'),
                    'created_by': teacher_a_user,
                },
            )

        eligible_a = [item for item in enrollments if item.school_id == school_a.pk and item.classroom_id == assignments['a_math'].classroom_id]
        if eligible_a:
            HomeworkSubmission.objects.update_or_create(
                homework=homework, student_enrollment=eligible_a[0],
                defaults={
                    'answer': 'DEMO submitted answer', 'status': 'graded',
                    'submitted_at': timezone.now(), 'grade': Decimal('9'),
                    'graded_by': teacher_a_user, 'graded_at': timezone.now(),
                },
            )

        # Results acceptance dataset. Keep all records deterministic and update-or-create so
        # repeated demo seeding never duplicates them. The first Grade 6/A School A
        # enrollment is demo_student_a_01.
        if eligible_a:
            result_student = StudentEnrollment.objects.get(
                student__user__username='demo_student_a_01', academic_year=year_a,
            )
            result_specs = (
                # title, exam type, assignment, term, date, max marks, score, remarks, published
                (
                    'DEMO Published Quiz', 'DEMO_QUIZ', assignments['a_math'],
                    a['terms']['current'], date(2025, 10, 15), '20', '18',
                    'DEMO quiz feedback: بداية ممتازة.', True,
                ),
                (
                    'DEMO Monthly Mathematics', 'DEMO_MONTHLY', assignments['a_math'],
                    a['terms']['current'], date(2025, 10, 22), '20', '18',
                    'استمر على هذا المستوى في الاختبارات الشهرية.', True,
                ),
                (
                    'DEMO Midterm Science', 'DEMO_MID', assignments['a_science_g6'],
                    a['terms']['current'], date(2025, 11, 5), '50', '42',
                    'فهم جيد للمفاهيم العلمية، راجع الأسئلة التطبيقية.', True,
                ),
                (
                    'DEMO Term Arabic', 'DEMO_TERM', assignments['a_arabic_g6'],
                    a['terms']['current'], date(2025, 11, 19), '30', '27',
                    'أداء متميز في القراءة والقواعد.', True,
                ),
                (
                    'DEMO Final Mathematics', 'DEMO_FINAL', assignments['a_math'],
                    a['terms']['current_2'], date(2026, 3, 15), '100', '86',
                    'نتيجة نهائية قوية مع فرصة لتحسين مسائل الهندسة.', True,
                ),
                (
                    'DEMO Unpublished Mathematics Result', 'DEMO_QUIZ', assignments['a_math'],
                    a['terms']['current_2'], date(2026, 3, 22), '20', '17',
                    'هذه النتيجة للاختبار فقط ويجب ألا تظهر للطالب.', False,
                ),
            )
            for (
                title, type_code, assignment, academic_term, exam_date, total, score, remarks, published
            ) in result_specs:
                exam_type = ExamType.objects.get(school=school_a, code=type_code)
                result_exam, _ = Exam.objects.update_or_create(
                    academic_term=academic_term,
                    teacher_assignment=assignment,
                    exam_type=exam_type,
                    title=title,
                    defaults={
                        'school': school_a, 'academic_year': year_a,
                        'created_by': teacher_a_user, 'exam_date': exam_date,
                        'total_marks': Decimal(total), 'status': 'published',
                    },
                )
                ExamResult.objects.update_or_create(
                    exam=result_exam, student_enrollment=result_student,
                    defaults={
                        'score': Decimal(score), 'status': 'present',
                        'workflow_status': 'approved', 'remarks': remarks,
                        'graded_by': teacher_a_user, 'approved_by': admin_a,
                        'is_published': published,
                        'published_at': timezone.now() if published else None,
                        'published_by': admin_a if published else None,
                    },
                )

        # Historical results acceptance uses the transferred demo student because it has
        # a real historical School A membership and a separate current School B context.
        historical_exam_type = ExamType.objects.get(school=school_a, code='DEMO_QUIZ')
        historical_exam, _ = Exam.objects.update_or_create(
            academic_term=a['terms']['previous'],
            teacher_assignment=assignments['a_math_previous'],
            exam_type=historical_exam_type,
            title='DEMO Historical Mathematics Quiz',
            defaults={
                'school': school_a, 'academic_year': a['years']['previous'],
                'created_by': teacher_a_user, 'exam_date': date(2024, 10, 20),
                'total_marks': Decimal('20'), 'status': 'published',
            },
        )
        ExamResult.objects.update_or_create(
            exam=historical_exam, student_enrollment=old_enrollment,
            defaults={
                'score': Decimal('14'), 'status': 'present',
                'workflow_status': 'approved',
                'remarks': 'نتيجة تاريخية تجريبية للعرض فقط.',
                'graded_by': teacher_a_user, 'approved_by': admin_a,
                'is_published': True, 'published_at': timezone.now(),
                'published_by': admin_a,
            },
        )

        announcement, _ = Announcement.objects.update_or_create(
            school=school_a, title='DEMO School Announcement',
            defaults={
                'academic_year': year_a, 'body': 'DEMO school-wide announcement',
                'status': 'published', 'audience_type': 'school',
                'created_by_membership': SchoolMembership.objects.get(user=admin_a, school=school_a),
                'published_by_membership': SchoolMembership.objects.get(user=admin_a, school=school_a),
                'published_at': timezone.now(),
            },
        )
        for membership in SchoolMembership.objects.filter(school=school_a, status='active').exclude(role='super_admin'):
            AnnouncementReceipt.objects.get_or_create(
                announcement=announcement, recipient_membership=membership,
            )
        AnnouncementReceipt.objects.get_or_create(
            announcement=announcement, recipient_membership=transferred_old_m,
        )
        announcement_b, _ = Announcement.objects.update_or_create(
            school=school_b, title='DEMO School B Announcement',
            defaults={
                'academic_year': year_b, 'body': 'DEMO school B announcement',
                'status': 'published', 'audience_type': 'roles', 'target_roles': ['student'],
                'created_by_membership': SchoolMembership.objects.get(user=admin_b, school=school_b),
                'published_by_membership': SchoolMembership.objects.get(user=admin_b, school=school_b),
                'published_at': timezone.now(),
            },
        )
        for membership in SchoolMembership.objects.filter(
            school=school_b, role='student', status='active',
        ):
            AnnouncementReceipt.objects.get_or_create(
                announcement=announcement_b, recipient_membership=membership,
            )
        Notification.objects.update_or_create(
            recipient_membership=teacher_a_m, deduplication_key='DEMO:system:welcome',
            defaults={
                'school': school_a, 'recipient': teacher_a_user, 'notification_type': 'system',
                'title': 'DEMO Welcome', 'body': 'DEMO notification',
                'source_type': 'demo', 'source_id': announcement.pk,
            },
        )
        Notification.objects.update_or_create(
            recipient_membership=transferred_current_m, deduplication_key='DEMO:transfer:current',
            defaults={
                'school': school_b, 'recipient': transferred_user, 'notification_type': 'system',
                'title': 'DEMO Current School', 'body': 'DEMO current membership notification',
                'source_type': 'demo', 'source_id': current_enrollment.pk,
            },
        )
        support, _ = Conversation.objects.update_or_create(
            school=school_a, conversation_type='school_support',
            subject='DEMO Academic Support',
            defaults={
                'created_by_membership': teacher_a_m, 'status': 'open',
                'category': 'academic_inquiry', 'priority': 'normal',
            },
        )
        ConversationParticipant.objects.update_or_create(
            conversation=support, membership=teacher_a_m,
            defaults={'participant_role': 'teacher', 'can_reply': True, 'is_active': True},
        )
        Message.objects.update_or_create(
            conversation=support, sender_membership=teacher_a_m,
            body='DEMO support message',
            defaults={'message_type': 'text'},
        )
        return {
            'schools': School.objects.filter(code__in=DEMO_SCHOOL_CODES).count(),
            'students': Student.objects.filter(user__username__startswith='demo_').count(),
            'attendance': Attendance.objects.filter(note='DEMO attendance').count(),
            'published_results': ExamResult.objects.filter(
                exam__school__code__in=DEMO_SCHOOL_CODES, is_published=True,
            ).count(),
            'super_admin': super_admin.pk, 'multi_membership': multi_a.pk,
        }
