from django.core import signing
from django.db import transaction
from django.db.models import Count
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .context import require_writable_context
from .models import (
    AcademicTerm, AcademicYear, Announcement, Attendance, Classroom, Conversation,
    Exam, Homework, Parent, SchoolPeriod, SchoolSetting, Section, Student,
    StudentEnrollment, StudentGuardian, Subject, Teacher, TeacherAssignment,
    TimetableEntry,
)
from .permissions import IsActiveSchoolUser


def _admin(request, write=False):
    if request.active_role not in ('school_admin', 'super_admin'):
        raise PermissionDenied('School administrator access is required.')
    if write:
        require_writable_context(request)
    if not request.active_school:
        raise PermissionDenied('Active school context is required.')


class SchoolSettingsAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    def _payload(self, request):
        school = request.active_school
        item, _ = SchoolSetting.objects.get_or_create(
            school=school,
            defaults={'school_name_ar': school.name},
        )
        return item

    def get(self, request):
        _admin(request)
        item = self._payload(request)
        return Response({
            'school': {'id': request.active_school.id, 'name': request.active_school.name,
                       'code': request.active_school.code, 'phone': request.active_school.phone,
                       'email': request.active_school.email, 'address': request.active_school.address},
            'settings': {'school_name_ar': item.school_name_ar, 'school_name_en': item.school_name_en or '',
                         'primary_color': item.primary_color, 'language': item.language,
                         'timezone': item.timezone,
                         'allow_parent_notifications': item.allow_parent_notifications},
        })

    def patch(self, request):
        _admin(request, write=True)
        item = self._payload(request)
        school = request.active_school
        school_fields = ('name', 'phone', 'email', 'address')
        setting_fields = ('school_name_ar', 'school_name_en', 'primary_color', 'language',
                          'timezone', 'allow_parent_notifications')
        for field in school_fields:
            if field in request.data:
                setattr(school, field, request.data[field])
        if 'name' in request.data and not request.data.get('school_name_ar'):
            item.school_name_ar = request.data['name']
        for field in setting_fields:
            if field in request.data:
                setattr(item, field, request.data[field])
        if item.language not in ('ar', 'en'):
            raise ValidationError({'language': 'Supported languages are ar and en.'})
        if item.primary_color and not str(item.primary_color).startswith('#'):
            raise ValidationError({'primary_color': 'Color must be a hex value.'})
        school.full_clean()
        changed_school_fields = [f for f in school_fields if f in request.data]
        if changed_school_fields:
            school.save(update_fields=changed_school_fields)
        item.full_clean(); item.save()
        return self.get(request)


class OnboardingStatusAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    def get(self, request):
        _admin(request)
        school, year = request.active_school, request.active_academic_year
        checks = [
            ('school', 'بيانات المدرسة', True),
            ('academic_year', 'السنة الدراسية', bool(year)),
            ('terms', 'الفصول الدراسية', bool(year and AcademicTerm.objects.filter(school=school, academic_year=year).exists())),
            ('classes', 'الصفوف', bool(year and Classroom.objects.filter(school=school, academic_year=year).exists())),
            ('sections', 'الشعب', bool(year and Section.objects.filter(school=school, academic_year=year).exists())),
            ('subjects', 'المواد', Subject.objects.filter(school=school, is_active=True).exists()),
            ('teachers', 'المعلمون', bool(year and Teacher.objects.filter(school=school, academic_year=year, is_active=True).exists())),
            ('assignments', 'تكليفات المعلمين', bool(year and TeacherAssignment.objects.filter(school=school, academic_year=year, is_current=True).exists())),
            ('students', 'الطلاب والتسجيلات', bool(year and StudentEnrollment.objects.filter(school=school, academic_year=year, status='active').exists())),
            ('timetable', 'الفترات والجدول', bool(year and SchoolPeriod.objects.filter(school=school, academic_year=year, is_active=True).exists())),
        ]
        done = sum(1 for _, _, value in checks if value)
        return Response({'ready': done == len(checks), 'completed': done, 'total': len(checks),
                         'progress': round(done * 100 / len(checks)),
                         'steps': [{'key': k, 'label': label, 'complete': value} for k, label, value in checks]})


class SafeRecipientDiscoveryAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    def _ref(self, request, kind, membership_id, student_id, assignment_id):
        return signing.dumps({'s': request.active_school.id, 'k': kind, 'm': membership_id,
                              'student': student_id, 'assignment': assignment_id},
                             salt='communication-recipient-v1', compress=True)

    def get(self, request):
        role, school, year = request.active_role, request.active_school, request.active_academic_year
        student_id = request.query_params.get('student_id')
        if not student_id:
            raise ValidationError({'student_id': 'student_id is required.'})
        try:
            student_id = int(student_id)
        except ValueError:
            raise ValidationError({'student_id': 'student_id must be an integer.'})
        enrollment = StudentEnrollment.objects.filter(
            student_id=student_id, school=school, academic_year=year, status='active',
        ).first()
        if not enrollment:
            raise PermissionDenied('Student is outside the active academic scope.')
        rows = []
        if role == 'teacher':
            own = TeacherAssignment.objects.filter(
                school=school, academic_year=year, teacher__user_id=request.user.id,
                classroom_id=enrollment.classroom_id, section_id=enrollment.section_id, is_current=True,
            ).first()
            if not own:
                raise PermissionDenied('Student is outside your teaching assignments.')
            links = StudentGuardian.objects.filter(student_id=student_id, parent__is_active=True).select_related('parent__user')
            for link in links:
                membership = getattr(link.parent.user, 'school_memberships', None)
                membership = membership.filter(school=school, role='parent', status='active').first() if membership else None
                if membership:
                    rows.append({'recipient_ref': self._ref(request, 'parent', membership.id, student_id, own.id),
                                 'display_name': link.parent.full_name, 'role': 'parent',
                                 'relationship': link.relationship, 'student_id': student_id})
        elif role == 'parent':
            if not StudentGuardian.objects.filter(student_id=student_id, parent__user_id=request.user.id).exists():
                raise PermissionDenied('Student is not linked to this parent.')
            assignments = TeacherAssignment.objects.filter(
                school=school, academic_year=year, classroom_id=enrollment.classroom_id,
                section_id=enrollment.section_id, is_current=True, teacher__is_active=True,
            ).select_related('teacher__user', 'subject')
            for assignment in assignments:
                membership = assignment.teacher.user.school_memberships.filter(
                    school=school, role='teacher', status='active',
                ).first() if assignment.teacher.user_id else None
                if membership:
                    rows.append({'recipient_ref': self._ref(request, 'teacher', membership.id, student_id, assignment.id),
                                 'display_name': assignment.teacher.full_name, 'role': 'teacher',
                                 'subject': assignment.subject.name, 'student_id': student_id,
                                 'teacher_assignment_id': assignment.id})
        else:
            raise PermissionDenied('Safe discovery is available to teachers and parents.')
        return Response({'results': rows})


class AdminReportSummaryAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    def get(self, request):
        _admin(request)
        school, year = request.active_school, request.active_academic_year
        enrollments = StudentEnrollment.objects.filter(school=school)
        attendance = Attendance.objects.filter(student_enrollment__school=school)
        homework = Homework.objects.filter(school=school)
        exams = Exam.objects.filter(school=school)
        if year:
            enrollments = enrollments.filter(academic_year=year)
            attendance = attendance.filter(student_enrollment__academic_year=year)
            homework = homework.filter(academic_year=year)
            exams = exams.filter(academic_year=year)
        status_counts = {row['status']: row['total'] for row in attendance.values('status').annotate(total=Count('id'))}
        total_att = sum(status_counts.values())
        attended = status_counts.get('present', 0) + status_counts.get('late', 0)
        return Response({
            'students': {'total': enrollments.values('student_id').distinct().count(),
                         'active': enrollments.filter(status='active').count()},
            'attendance': {'total': total_att, 'present': status_counts.get('present', 0),
                           'absent': status_counts.get('absent', 0), 'late': status_counts.get('late', 0),
                           'excused': status_counts.get('excused', 0),
                           'rate': round(attended * 100 / total_att, 2) if total_att else 0},
            'homework': {'total': homework.count(), 'published': homework.filter(status='published').count()},
            'exams': {'total': exams.count(), 'published': exams.filter(status='published').count()},
            'operations': {'teachers': Teacher.objects.filter(school=school, is_active=True).count(),
                           'parents': Parent.objects.filter(school=school, is_active=True).count(),
                           'conversations': Conversation.objects.filter(school=school).count(),
                           'announcements': Announcement.objects.filter(school=school).count()},
        })


class DataExportAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    def get(self, request):
        _admin(request)
        kind = request.query_params.get('kind', 'students')
        school, year = request.active_school, request.active_academic_year
        if kind == 'students':
            qs = StudentEnrollment.objects.filter(school=school)
            if year: qs = qs.filter(academic_year=year)
            rows = qs.select_related('student','classroom','section').values(
                'student__student_code','student__full_name','student__gender','classroom__name','section__name','status')
        elif kind == 'teachers':
            qs = Teacher.objects.filter(school=school)
            if year: qs = qs.filter(academic_year=year)
            rows = qs.values('employee_code','full_name','phone','email','specialization','is_active')
        else:
            raise ValidationError({'kind': 'Supported exports are students and teachers.'})
        return Response({'kind': kind, 'rows': list(rows)})


class DataImportAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    def post(self, request):
        _admin(request, write=True)
        kind, rows = request.data.get('kind'), request.data.get('rows')
        if kind not in ('students', 'teachers') or not isinstance(rows, list):
            raise ValidationError('kind and rows are required.')
        if len(rows) > 1000:
            raise ValidationError('A single import is limited to 1000 rows.')
        from .student_admin_serializers import StudentAdminWriteSerializer
        from .academic_serializers import TeacherAdminSerializer
        serializer_class = StudentAdminWriteSerializer if kind == 'students' else TeacherAdminSerializer
        valid, errors = [], []
        for index, row in enumerate(rows, start=2):
            serializer = serializer_class(data=row, context={'request': request})
            if serializer.is_valid():
                valid.append(serializer)
            else:
                errors.append({'row': index, 'errors': serializer.errors})
        if errors:
            return Response({'valid': False, 'created': 0, 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        created = []
        with transaction.atomic():
            for serializer in valid:
                item = serializer.save()
                created.append(item.pk)
        return Response({'valid': True, 'created': len(created), 'ids': created}, status=status.HTTP_201_CREATED)
