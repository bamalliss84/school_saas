import uuid
from datetime import date

from django import forms
from django.core import signing
from django.db import transaction
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .context import require_writable_context
from .models import (
    AcademicTerm, AcademicYear, Announcement, Attendance, Classroom, Conversation,
    Exam, Homework, HomeworkSubmission, Parent, SchoolPeriod, SchoolSetting, Section, Student,
    StudentEnrollment, StudentGuardian, Subject, Teacher, TeacherAssignment,
    TimetableEntry,
)
from .permissions import IsActiveSchoolUser
from .services import data_exchange, identity


def _admin(request, write=False):
    if request.active_role not in ('school_admin', 'super_admin'):
        raise PermissionDenied('School administrator access is required.')
    if write:
        require_writable_context(request)
    if not request.active_school:
        raise PermissionDenied('Active school context is required.')


def _int_param(request, name):
    value = request.query_params.get(name)
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError({name: f'{name} must be an integer.'})


def _date_param(request, name):
    value = request.query_params.get(name)
    if value in (None, ''):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationError({name: f'{name} must be a date in YYYY-MM-DD format.'})


class SchoolSettingsAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    def _payload(self, request):
        school = request.active_school
        item = SchoolSetting.objects.filter(school=school).first()
        return item or SchoolSetting(school=school, school_name_ar=school.name)

    def get(self, request):
        _admin(request)
        item = self._payload(request)
        return Response({
            'school': {'id': request.active_school.id, 'name': request.active_school.name,
                       'code': request.active_school.code, 'phone': request.active_school.phone,
                       'email': request.active_school.email, 'address': request.active_school.address},
            'settings': {'school_name_ar': item.school_name_ar, 'school_name_en': item.school_name_en or '',
                         'logo_url': request.build_absolute_uri(item.logo.url) if item.logo else None,
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
        try:
            school.full_clean()
            item.full_clean()
        except Exception as exc:
            raise ValidationError(getattr(exc, 'message_dict', {'detail': str(exc)}))
        changed_school_fields = [f for f in school_fields if f in request.data]
        with transaction.atomic():
            if changed_school_fields:
                school.save(update_fields=changed_school_fields)
            item.save()
        return self.get(request)


LOGO_MAX_BYTES = 2 * 1024 * 1024
LOGO_FORMATS = {'PNG': 'png', 'JPEG': 'jpg', 'WEBP': 'webp'}


class SchoolLogoAPIView(APIView):
    """Upload or remove the active school's logo (GAP-SET-01).

    Only raster PNG/JPEG/WEBP images verified by Pillow are accepted; SVG and
    other formats are rejected. Old files are removed only after commit.
    """
    permission_classes = (IsActiveSchoolUser,)
    parser_classes = (MultiPartParser,)

    def post(self, request):
        _admin(request, write=True)
        upload = request.FILES.get('logo')
        if upload is None:
            raise ValidationError({'logo': 'A logo image file is required.'})
        if upload.size > LOGO_MAX_BYTES:
            raise ValidationError({'logo': 'The logo must be 2 MB or smaller.'})
        try:
            image = forms.ImageField().clean(upload)
        except forms.ValidationError:
            raise ValidationError({'logo': 'Upload a valid PNG, JPEG or WEBP image.'})
        extension = LOGO_FORMATS.get(getattr(image.image, 'format', None))
        if extension is None:
            raise ValidationError({'logo': 'Upload a valid PNG, JPEG or WEBP image.'})
        upload.seek(0)
        school = request.active_school
        with transaction.atomic():
            item = SchoolSetting.objects.select_for_update().filter(school=school).first() or SchoolSetting(
                school=school, school_name_ar=school.name,
            )
            old_name = item.logo.name if item.logo else None
            item.logo.save(f'school-{school.pk}-{uuid.uuid4().hex}.{extension}', upload, save=False)
            item.save()
            if old_name:
                storage = item.logo.storage
                transaction.on_commit(lambda: storage.delete(old_name))
        return Response({'logo_url': request.build_absolute_uri(item.logo.url)}, status=status.HTTP_200_OK)

    def delete(self, request):
        _admin(request, write=True)
        with transaction.atomic():
            item = SchoolSetting.objects.select_for_update().filter(school=request.active_school).first()
            if item and item.logo:
                old_name, storage = item.logo.name, item.logo.storage
                item.logo = None
                item.save()
                transaction.on_commit(lambda: storage.delete(old_name))
        return Response(status=status.HTTP_204_NO_CONTENT)


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
            ('teachers', 'المعلمون', Teacher.objects.filter(school=school, is_active=True).exists()),
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
            )
            assignment_id = request.query_params.get('teacher_assignment_id')
            if assignment_id:
                try:
                    own = own.filter(pk=int(assignment_id))
                except ValueError:
                    raise ValidationError({'teacher_assignment_id': 'teacher_assignment_id must be an integer.'})
            own = own.order_by('pk').first()
            if not own:
                raise PermissionDenied('Student is outside your teaching assignments.')
            links = StudentGuardian.objects.filter(student_id=student_id, parent__is_active=True).select_related('parent__user')
            for link in links:
                membership = getattr(link.parent.user, 'school_memberships', None)
                membership = membership.filter(school=school, role='parent', status='active').first() if membership else None
                if membership:
                    rows.append({'recipient_ref': self._ref(request, 'parent', membership.id, student_id, own.id),
                                 'display_name': link.parent.full_name, 'role': 'parent',
                                 'relationship': link.relationship, 'student_id': student_id,
                                 'teacher_assignment_id': own.id})
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
        submissions = HomeworkSubmission.objects.filter(homework__school=school)
        exams = Exam.objects.filter(school=school)
        filters = {}
        if year:
            enrollments = enrollments.filter(academic_year=year)
            attendance = attendance.filter(student_enrollment__academic_year=year)
            homework = homework.filter(academic_year=year)
            submissions = submissions.filter(homework__academic_year=year)
            exams = exams.filter(academic_year=year)
        classroom_id = _int_param(request, 'classroom_id')
        section_id = _int_param(request, 'section_id')
        student_id = _int_param(request, 'student_id')
        date_from = _date_param(request, 'date_from')
        date_to = _date_param(request, 'date_to')
        if date_from and date_to and date_from > date_to:
            raise ValidationError({'date_to': 'date_to must be on or after date_from.'})
        if classroom_id:
            filters['classroom_id'] = str(classroom_id)
            enrollments = enrollments.filter(classroom_id=classroom_id)
            attendance = attendance.filter(student_enrollment__classroom_id=classroom_id)
            homework = homework.filter(teacher_assignment__classroom_id=classroom_id)
            submissions = submissions.filter(homework__teacher_assignment__classroom_id=classroom_id)
            exams = exams.filter(teacher_assignment__classroom_id=classroom_id)
        if section_id:
            filters['section_id'] = str(section_id)
            enrollments = enrollments.filter(section_id=section_id)
            attendance = attendance.filter(student_enrollment__section_id=section_id)
            homework = homework.filter(teacher_assignment__section_id=section_id)
            submissions = submissions.filter(homework__teacher_assignment__section_id=section_id)
            exams = exams.filter(teacher_assignment__section_id=section_id)
        if student_id:
            filters['student_id'] = str(student_id)
            enrollments = enrollments.filter(student_id=student_id)
            attendance = attendance.filter(student_enrollment__student_id=student_id)
            submissions = submissions.filter(student_enrollment__student_id=student_id)
        if date_from:
            filters['date_from'] = date_from.isoformat()
            attendance = attendance.filter(attendance_date__gte=date_from)
            homework = homework.filter(due_date__date__gte=date_from)
            submissions = submissions.filter(homework__due_date__date__gte=date_from)
        if date_to:
            filters['date_to'] = date_to.isoformat()
            attendance = attendance.filter(attendance_date__lte=date_to)
            homework = homework.filter(due_date__date__lte=date_to)
            submissions = submissions.filter(homework__due_date__date__lte=date_to)
        status_counts = {row['status']: row['total'] for row in attendance.values('status').annotate(total=Count('id'))}
        total_att = sum(status_counts.values())
        attended = status_counts.get('present', 0) + status_counts.get('late', 0)
        submission_counts = {row['status']: row['total'] for row in submissions.values('status').annotate(total=Count('id'))}
        submitted = sum(submission_counts.get(x, 0) for x in ('submitted', 'graded', 'reviewed'))
        expected_submissions = 0
        for item in homework.filter(status__in=('published', 'closed')).values(
            'teacher_assignment__classroom_id', 'teacher_assignment__section_id'
        ):
            expected_submissions += enrollments.filter(
                classroom_id=item['teacher_assignment__classroom_id'],
                section_id=item['teacher_assignment__section_id'], status='active',
            ).count()
        return Response({
            'filters': filters,
            'students': {'total': enrollments.values('student_id').distinct().count(),
                         'active': enrollments.filter(status='active').count()},
            'attendance': {'total': total_att, 'present': status_counts.get('present', 0),
                           'absent': status_counts.get('absent', 0), 'late': status_counts.get('late', 0),
                           'excused': status_counts.get('excused', 0),
                           'rate': round(attended * 100 / total_att, 2) if total_att else 0},
            'homework': {'total': homework.count(), 'published': homework.filter(status='published').count(),
                         'submissions': submissions.count(), 'submitted': submitted,
                         'not_submitted': max(expected_submissions - submitted, 0),
                         'completion_rate': round(submitted * 100 / expected_submissions, 2) if expected_submissions else 0},
            'exams': {'total': exams.count(), 'published': exams.filter(status='published').count()},
            'operations': {'teachers': TeacherAssignment.objects.filter(
                                school=school, academic_year=year, is_current=True, teacher__is_active=True
                            ).values('teacher_id').distinct().count() if year else TeacherAssignment.objects.filter(
                                school=school, is_current=True, teacher__is_active=True
                            ).values('teacher_id').distinct().count(),
                           'parents': Parent.objects.filter(
                               Q(school=school) | Q(students__student__enrollments__school=school), is_active=True
                           ).distinct().count(),
                           'conversations': Conversation.objects.filter(school=school).count(),
                           'announcements': Announcement.objects.filter(school=school).count()},
        })


class DataExportAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    def get(self, request):
        _admin(request)
        kind = request.query_params.get('kind', 'students')
        output = request.query_params.get('output', 'json')
        if output not in ('json', 'xlsx'):
            raise ValidationError({'output': 'Supported outputs are json and xlsx.'})
        school, year = request.active_school, request.active_academic_year
        if kind in data_exchange.OPERATIONAL_KINDS:
            filters = {
                'date_from': _date_param(request, 'date_from'), 'date_to': _date_param(request, 'date_to'),
                'classroom_id': _int_param(request, 'classroom_id'), 'section_id': _int_param(request, 'section_id'),
            }
            if filters['date_from'] and filters['date_to'] and filters['date_from'] > filters['date_to']:
                raise ValidationError({'date_from': 'date_from must not be after date_to.'})
            rows = data_exchange.operational_rows(school, year, kind, filters)
        elif kind == 'students':
            qs = StudentEnrollment.objects.filter(school=school)
            if year: qs = qs.filter(academic_year=year)
            rows = [
                {'student_code': e.student.student_code, 'full_name': e.student.full_name,
                 'gender': e.student.gender, 'classroom': e.classroom.name,
                 'section': e.section.name, 'status': e.status}
                for e in qs.select_related('student', 'classroom', 'section')
            ]
        elif kind == 'teachers':
            qs = Teacher.objects.filter(school=school)
            if year: qs = qs.filter(academic_year=year)
            rows = qs.values('employee_code','full_name','phone','email','specialization','is_active')
        elif kind == 'guardians':
            qs = StudentGuardian.objects.filter(
                student__enrollments__school=school,
            ).select_related('student', 'parent').distinct()
            if year:
                qs = qs.filter(student__enrollments__academic_year=year)
            rows = [{
                'student_code': link.student.student_code,
                'full_name': link.parent.full_name,
                'national_id': link.parent.national_id,
                'phone': link.parent.phone, 'email': link.parent.email,
                'relationship': link.relationship, 'is_primary': link.is_primary,
                'can_receive_notifications': link.can_receive_notifications,
                'can_receive_financial_alerts': link.can_receive_financial_alerts,
            } for link in qs]
        else:
            raise ValidationError({'kind': 'Supported exports are: ' + ', '.join(data_exchange.EXPORT_KINDS) + '.'})
        rows = list(rows)
        if output == 'xlsx':
            return data_exchange.export_response(kind, rows)
        return Response({'kind': kind, 'rows': rows})


class DataImportTemplateAPIView(APIView):
    """F1L-6: an Excel import template with Arabic headers and text-formatted code columns."""
    permission_classes = (IsActiveSchoolUser,)

    def get(self, request):
        _admin(request)
        return data_exchange.template_response(request.query_params.get('kind', 'students'))


class DataImportParseAPIView(APIView):
    """F1L-6: turn an uploaded .xlsx into rows for the existing preview -> confirm import."""
    permission_classes = (IsActiveSchoolUser,)
    parser_classes = (MultiPartParser,)

    def post(self, request):
        _admin(request, write=True)
        return Response(data_exchange.parse_import(request.data.get('kind'), request.FILES.get('file')))


class DataImportAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    def post(self, request):
        _admin(request, write=True)
        kind, rows = request.data.get('kind'), request.data.get('rows')
        if kind not in ('students', 'teachers', 'guardians') or not isinstance(rows, list):
            raise ValidationError('kind and rows are required.')
        if len(rows) > 1000:
            raise ValidationError('A single import is limited to 1000 rows.')
        from .student_admin_serializers import StudentAdminWriteSerializer
        from .academic_serializers import TeacherAdminSerializer
        serializer_class = StudentAdminWriteSerializer if kind == 'students' else TeacherAdminSerializer
        valid, errors = [], []
        for index, row in enumerate(rows, start=2):
            if kind == 'guardians':
                student_code = str(row.get('student_code', '')).strip()
                full_name = str(row.get('full_name', '')).strip()
                relationship = str(row.get('relationship', '')).strip()
                student = Student.objects.filter(
                    school=request.active_school, student_code=student_code, is_active=True,
                ).first()
                if not student:
                    errors.append({'row': index, 'errors': {'student_code': ['Student was not found in the active school.']}})
                    continue
                if not full_name or relationship not in dict(StudentGuardian.RELATION_CHOICES):
                    errors.append({'row': index, 'errors': {'guardian': ['full_name and a valid relationship are required.']}})
                    continue
                username = str(row.get('account_username', '')).strip()
                from django.contrib.auth import get_user_model
                if username and get_user_model().objects.filter(username=username).exists():
                    errors.append({'row': index, 'errors': {'account_username': ['Username already exists.']}})
                    continue
                valid.append({'row': row, 'student': student})
                continue
            serializer = serializer_class(data=row, context={'request': request})
            if serializer.is_valid():
                valid.append(serializer)
            else:
                errors.append({'row': index, 'errors': serializer.errors})
        if errors:
            return Response({'valid': False, 'created': 0, 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        # Validation/preview is deliberately separate from the committing step.
        # The client must explicitly confirm after showing the validated preview.
        confirm = request.data.get('confirm') is True
        if not confirm:
            return Response({
                'valid': True, 'confirmed': False, 'created': 0,
                'preview_count': len(valid), 'preview': rows[:50], 'errors': [],
            })
        created = []
        with transaction.atomic():
            for serializer in valid:
                if kind == 'guardians':
                    row, student = serializer['row'], serializer['student']
                    username = str(row.get('account_username', '')).strip()
                    password = str(row.get('account_password', '')).strip()
                    parent = identity.create_parent_with_guardian(
                        school=request.active_school, student=student,
                        parent_values={
                            'full_name': str(row.get('full_name', '')).strip(),
                            'national_id': str(row.get('national_id', '')).strip(),
                            'phone': str(row.get('phone', '')).strip(),
                            'email': str(row.get('email', '')).strip(),
                            'address': str(row.get('address', '')).strip(),
                            'occupation': str(row.get('occupation', '')).strip(),
                            'workplace': str(row.get('workplace', '')).strip(),
                        },
                        guardian_values={
                            'relationship': str(row.get('relationship', '')).strip(),
                            'is_primary': str(row.get('is_primary', '')).lower() in ('1', 'true', 'yes'),
                            'can_receive_notifications': str(row.get('can_receive_notifications', 'true')).lower() not in ('0', 'false', 'no'),
                            'can_receive_financial_alerts': str(row.get('can_receive_financial_alerts', 'true')).lower() not in ('0', 'false', 'no'),
                        },
                        account_username=username or None, account_password=password or None,
                    )
                    created.append(parent.pk)
                else:
                    item = serializer.save()
                    created.append(item.pk)
        return Response({
            'valid': True, 'confirmed': True, 'created': len(created), 'ids': created,
        }, status=status.HTTP_201_CREATED)
