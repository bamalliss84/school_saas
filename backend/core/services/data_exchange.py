"""Admin data exchange: Excel templates, import parsing and operational exports.

Every query is scoped to the active school and, when present, the active
academic year (historical contexts export their own year read-only). Import
parsing only converts a workbook into the rows the existing JSON import
endpoint validates, previews and confirms; it never writes data itself.
"""
from django.db.models import Count
from django.http import HttpResponse
from rest_framework.exceptions import ValidationError

from core.models import Attendance, ExamResult, Homework, TimetableEntry

from . import spreadsheets

IMPORT_KINDS = ('students', 'teachers', 'guardians')
OPERATIONAL_KINDS = ('attendance', 'results', 'timetable', 'homework')
EXPORT_KINDS = IMPORT_KINDS + OPERATIONAL_KINDS
MAX_EXPORT_ROWS = 20000

# Identifier-like columns stay text in Excel so leading zeros are not lost.
TEXT_COLUMNS = frozenset({
    'student_code', 'employee_code', 'phone', 'national_id', 'account_username',
})

IMPORT_COLUMNS = {
    'students': [
        ('full_name', 'الاسم الكامل'), ('gender', 'الجنس'), ('birth_date', 'تاريخ الميلاد'),
    ],
    'teachers': [
        ('full_name', 'الاسم الكامل'), ('phone', 'الجوال'), ('email', 'البريد الإلكتروني'),
        ('specialization', 'التخصص'), ('qualification', 'المؤهل'), ('hire_date', 'تاريخ التعيين'),
        ('address', 'العنوان'), ('account_username', 'اسم المستخدم'),
    ],
    'guardians': [
        ('student_code', 'كود الطالب'), ('full_name', 'اسم ولي الأمر'), ('relationship', 'صلة القرابة'),
        ('national_id', 'رقم الهوية'), ('phone', 'الجوال'), ('email', 'البريد الإلكتروني'),
        ('address', 'العنوان'), ('occupation', 'المهنة'), ('workplace', 'جهة العمل'),
        ('is_primary', 'ولي الأمر الأساسي'), ('can_receive_notifications', 'يستقبل الإشعارات'),
        ('can_receive_financial_alerts', 'يستقبل التنبيهات المالية'), ('account_username', 'اسم المستخدم'),
    ],
}
# Accepted by the import serializers but deliberately absent from templates:
# passwords should not travel in spreadsheets.
EXTRA_IMPORT_KEYS = {'teachers': ('account_password',), 'guardians': ('account_password',)}
REQUIRED_IMPORT_KEYS = {
    'students': ('full_name', 'gender'), 'teachers': ('full_name',),
    'guardians': ('student_code', 'full_name', 'relationship'),
}
TEMPLATE_NOTES = {
    'students': [
        'الجنس: ذكر أو أنثى.', 'تاريخ الميلاد بصيغة YYYY-MM-DD.',
        'يُنشأ كود الطالب تلقائيًا، وتسجيل الطالب في الصف يتم من صفحة الطلاب.',
    ],
    'teachers': [
        'يُنشأ رقم الموظف تلقائيًا.', 'تاريخ التعيين بصيغة YYYY-MM-DD.',
        'اسم المستخدم اختياري؛ كلمة المرور لا تُكتب في الملف وتُعيَّن من النظام.',
    ],
    'guardians': [
        'كود الطالب يجب أن يكون لطالب نشط في المدرسة الحالية.',
        'صلة القرابة: أب، أم، أخ، أخت، ولي أمر، أخرى.',
        'الأعمدة نعم/لا: ولي الأمر الأساسي، يستقبل الإشعارات، يستقبل التنبيهات المالية.',
    ],
}
VALUE_ALIASES = {
    'gender': {'ذكر': 'male', 'أنثى': 'female', 'انثى': 'female'},
    'relationship': {
        'أب': 'father', 'اب': 'father', 'أم': 'mother', 'ام': 'mother', 'أخ': 'brother', 'اخ': 'brother',
        'أخت': 'sister', 'اخت': 'sister', 'ولي أمر': 'guardian', 'ولي امر': 'guardian', 'أخرى': 'other', 'اخرى': 'other',
    },
}
BOOLEAN_KEYS = ('is_primary', 'can_receive_notifications', 'can_receive_financial_alerts')
BOOLEAN_ALIASES = {'نعم': 'true', 'لا': 'false'}

STATUS_LABELS = {
    'present': 'حاضر', 'absent': 'غائب', 'late': 'متأخر', 'excused': 'بعذر',
    'not_graded': 'لم يُرصد', 'exempted': 'معفى',
    'draft': 'مسودة', 'published': 'منشور', 'closed': 'مغلق', 'cancelled': 'ملغى',
    'active': 'نشط', 'transferred': 'منقول', 'graduated': 'متخرج', 'withdrawn': 'منسحب', 'suspended': 'موقوف',
}
WEEKDAY_LABELS = {0: 'الأحد', 1: 'الاثنين', 2: 'الثلاثاء', 3: 'الأربعاء', 4: 'الخميس', 5: 'الجمعة', 6: 'السبت'}

EXPORT_COLUMNS = {
    'students': [
        ('student_code', 'كود الطالب'), ('full_name', 'الاسم'), ('gender', 'الجنس'),
        ('classroom', 'الصف'), ('section', 'الشعبة'), ('status', 'الحالة'),
    ],
    'teachers': [
        ('employee_code', 'رقم الموظف'), ('full_name', 'الاسم'), ('phone', 'الجوال'),
        ('email', 'البريد الإلكتروني'), ('specialization', 'التخصص'), ('is_active', 'نشط'),
    ],
    'guardians': [
        ('student_code', 'كود الطالب'), ('full_name', 'اسم ولي الأمر'), ('national_id', 'رقم الهوية'),
        ('phone', 'الجوال'), ('email', 'البريد الإلكتروني'), ('relationship', 'صلة القرابة'),
        ('is_primary', 'أساسي'), ('can_receive_notifications', 'يستقبل الإشعارات'),
        ('can_receive_financial_alerts', 'يستقبل التنبيهات المالية'),
    ],
    'attendance': [
        ('attendance_date', 'التاريخ'), ('student_code', 'كود الطالب'), ('student_name', 'الطالب'),
        ('classroom', 'الصف'), ('section', 'الشعبة'), ('subject', 'المادة'), ('teacher', 'المعلم'),
        ('status', 'الحالة'), ('note', 'ملاحظة'),
    ],
    'results': [
        ('exam_date', 'تاريخ الاختبار'), ('exam', 'الاختبار'), ('exam_type', 'النوع'), ('subject', 'المادة'),
        ('classroom', 'الصف'), ('section', 'الشعبة'), ('student_code', 'كود الطالب'),
        ('student_name', 'الطالب'), ('score', 'الدرجة'), ('total_marks', 'الدرجة الكاملة'),
        ('status', 'حالة الرصد'), ('workflow_status', 'حالة الاعتماد'),
    ],
    'timetable': [
        ('weekday', 'اليوم'), ('period', 'الفترة'), ('start_time', 'البداية'), ('end_time', 'النهاية'),
        ('classroom', 'الصف'), ('section', 'الشعبة'), ('subject', 'المادة'), ('teacher', 'المعلم'),
        ('room', 'القاعة'), ('valid_from', 'ساري من'), ('valid_to', 'ساري حتى'),
    ],
    'homework': [
        ('title', 'الواجب'), ('classroom', 'الصف'), ('section', 'الشعبة'), ('subject', 'المادة'),
        ('teacher', 'المعلم'), ('status', 'الحالة'), ('published_at', 'تاريخ النشر'),
        ('due_date', 'موعد التسليم'), ('max_grade', 'الدرجة الكاملة'), ('submissions', 'عدد التسليمات'),
    ],
}
SHEET_TITLES = {
    'students': 'الطلاب', 'teachers': 'المعلمون', 'guardians': 'أولياء الأمور', 'attendance': 'الحضور',
    'results': 'النتائج', 'timetable': 'الجدول', 'homework': 'الواجبات',
}


def _cap(queryset):
    if queryset.count() > MAX_EXPORT_ROWS:
        raise ValidationError(
            {'detail': f'The export exceeds {MAX_EXPORT_ROWS} rows; narrow the date range or class filter.'},
        )
    return queryset


def _assignment_filter(prefix, filters):
    lookups = {}
    if filters.get('classroom_id'):
        lookups[f'{prefix}classroom_id'] = filters['classroom_id']
    if filters.get('section_id'):
        lookups[f'{prefix}section_id'] = filters['section_id']
    return lookups


def operational_rows(school, year, kind, filters):
    date_from, date_to = filters.get('date_from'), filters.get('date_to')
    if kind == 'attendance':
        qs = Attendance.objects.filter(student_enrollment__school=school)
        if year:
            qs = qs.filter(student_enrollment__academic_year=year)
        if date_from:
            qs = qs.filter(attendance_date__gte=date_from)
        if date_to:
            qs = qs.filter(attendance_date__lte=date_to)
        qs = qs.filter(**_assignment_filter('student_enrollment__', filters)).select_related(
            'student_enrollment__student', 'student_enrollment__classroom', 'student_enrollment__section',
            'teacher_assignment__subject', 'teacher_assignment__teacher',
        ).order_by('attendance_date', 'student_enrollment__classroom__name', 'student_enrollment__student__full_name')
        return [{
            'attendance_date': item.attendance_date,
            'student_code': item.student_enrollment.student.student_code,
            'student_name': item.student_enrollment.student.full_name,
            'classroom': item.student_enrollment.classroom.name,
            'section': item.student_enrollment.section.name,
            'subject': item.teacher_assignment.subject.name if item.teacher_assignment_id else '',
            'teacher': item.teacher_assignment.teacher.full_name if item.teacher_assignment_id else '',
            'status': STATUS_LABELS.get(item.status, item.status), 'note': item.note or '',
        } for item in _cap(qs)]
    if kind == 'results':
        qs = ExamResult.objects.filter(exam__school=school)
        if year:
            qs = qs.filter(exam__academic_year=year)
        if date_from:
            qs = qs.filter(exam__exam_date__gte=date_from)
        if date_to:
            qs = qs.filter(exam__exam_date__lte=date_to)
        qs = qs.filter(**_assignment_filter('exam__teacher_assignment__', filters)).select_related(
            'exam__exam_type', 'exam__teacher_assignment__subject', 'exam__teacher_assignment__classroom',
            'exam__teacher_assignment__section', 'student_enrollment__student',
        ).order_by('exam__exam_date', 'exam__title', 'student_enrollment__student__full_name')
        return [{
            'exam_date': item.exam.exam_date, 'exam': item.exam.title,
            'exam_type': item.exam.exam_type.name if item.exam.exam_type_id else '',
            'subject': item.exam.teacher_assignment.subject.name,
            'classroom': item.exam.teacher_assignment.classroom.name,
            'section': item.exam.teacher_assignment.section.name,
            'student_code': item.student_enrollment.student.student_code,
            'student_name': item.student_enrollment.student.full_name,
            'score': item.score, 'total_marks': item.exam.total_marks,
            'status': STATUS_LABELS.get(item.status, item.status), 'workflow_status': item.workflow_status,
        } for item in _cap(qs)]
    if kind == 'timetable':
        qs = TimetableEntry.objects.filter(school=school, is_active=True)
        if year:
            qs = qs.filter(academic_year=year)
        qs = qs.filter(**_assignment_filter('teacher_assignment__', filters)).select_related(
            'period', 'teacher_assignment__classroom', 'teacher_assignment__section',
            'teacher_assignment__subject', 'teacher_assignment__teacher',
        ).order_by('teacher_assignment__classroom__name', 'teacher_assignment__section__name', 'weekday', 'period__sequence')
        return [{
            'weekday': WEEKDAY_LABELS.get(item.weekday, item.weekday), 'period': item.period.name,
            'start_time': item.period.start_time.strftime('%H:%M'), 'end_time': item.period.end_time.strftime('%H:%M'),
            'classroom': item.teacher_assignment.classroom.name, 'section': item.teacher_assignment.section.name,
            'subject': item.teacher_assignment.subject.name, 'teacher': item.teacher_assignment.teacher.full_name,
            'room': item.room_or_location, 'valid_from': item.valid_from, 'valid_to': item.valid_to,
        } for item in _cap(qs)]
    if kind == 'homework':
        qs = Homework.objects.filter(school=school)
        if year:
            qs = qs.filter(academic_year=year)
        if date_from:
            qs = qs.filter(due_date__date__gte=date_from)
        if date_to:
            qs = qs.filter(due_date__date__lte=date_to)
        qs = qs.filter(**_assignment_filter('teacher_assignment__', filters)).select_related(
            'teacher_assignment__classroom', 'teacher_assignment__section',
            'teacher_assignment__subject', 'teacher_assignment__teacher',
        ).annotate(submission_count=Count('submissions')).order_by('due_date', 'pk')
        return [{
            'title': item.title, 'classroom': item.teacher_assignment.classroom.name,
            'section': item.teacher_assignment.section.name, 'subject': item.teacher_assignment.subject.name,
            'teacher': item.teacher_assignment.teacher.full_name,
            'status': STATUS_LABELS.get(item.status, item.status),
            'published_at': item.published_at, 'due_date': item.due_date,
            'max_grade': item.max_grade, 'submissions': item.submission_count,
        } for item in _cap(qs)]
    raise ValidationError({'kind': 'Unsupported export kind.'})


def _xlsx_response(content, filename):
    response = HttpResponse(content, content_type=spreadsheets.XLSX_CONTENT_TYPE)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


def export_response(kind, rows):
    content = spreadsheets.build_xlsx(
        EXPORT_COLUMNS[kind], rows, sheet_title=SHEET_TITLES[kind], text_columns=TEXT_COLUMNS,
    )
    return _xlsx_response(content, f'{kind}-export.xlsx')


def template_response(kind):
    if kind not in IMPORT_KINDS:
        raise ValidationError({'kind': 'Templates are available for students, teachers and guardians.'})
    content = spreadsheets.build_xlsx(
        IMPORT_COLUMNS[kind], [], sheet_title=SHEET_TITLES[kind], text_columns=TEXT_COLUMNS,
        notes=TEMPLATE_NOTES[kind],
    )
    return _xlsx_response(content, f'{kind}-import-template.xlsx')


def parse_import(kind, upload):
    """Convert an uploaded workbook into import rows keyed by API field names."""
    if kind not in IMPORT_KINDS:
        raise ValidationError({'kind': 'Supported imports are students, teachers and guardians.'})
    headers, raw_rows = spreadsheets.read_xlsx_rows(upload)
    by_label = {}
    for key, label in IMPORT_COLUMNS[kind]:
        by_label[key.lower()] = key
        by_label[label] = key
    for key in EXTRA_IMPORT_KEYS.get(kind, ()):
        by_label[key] = key
    mapping, unknown = {}, []
    for header in headers:
        key = by_label.get(header) or by_label.get(header.lower())
        if key:
            mapping[header] = key
        else:
            unknown.append(header)
    if unknown:
        raise ValidationError({'columns': [f'Unknown column: {name}' for name in unknown]})
    missing = [key for key in REQUIRED_IMPORT_KEYS[kind] if key not in mapping.values()]
    if missing:
        labels = dict(IMPORT_COLUMNS[kind])
        raise ValidationError({'columns': [f'Missing required column: {labels.get(key, key)}' for key in missing]})
    rows = []
    for raw in raw_rows:
        row = {}
        for header, key in mapping.items():
            value = raw.get(header, '')
            value = VALUE_ALIASES.get(key, {}).get(value, value)
            if key in BOOLEAN_KEYS:
                value = BOOLEAN_ALIASES.get(value, value)
            if value != '':
                row[key] = value
        rows.append(row)
    if not rows:
        raise ValidationError({'file': 'The sheet has no data rows.'})
    return {'kind': kind, 'columns': list(mapping.values()), 'rows': rows}

