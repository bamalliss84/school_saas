from django.contrib import admin
from .models import School, AcademicYear, SchoolSetting, User
from django.contrib.auth.admin import UserAdmin
from .models import Classroom, Section, Subject, ClassSubject, Teacher, Parent, Student, StudentEnrollment
from .models import StudentGuardian, TeacherAssignment,AcademicTerm,Attendance,ExamType,Exam,ExamResult
from .models import ExamResultLog

class SchoolAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'code',
        'phone',
        'is_active',
        'created_at',
    )

    search_fields = (
        'name',
        'code',
        'phone',
    )

    list_filter = (
        'is_active',
    )

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'school',
        'name',
        'start_date',
        'end_date',
        'is_active',
    )

    search_fields = (
        'name',
        'school__name',
    )

    list_filter = (
        'school',
        'is_active',
    )

@admin.register(SchoolSetting)
class SchoolSettingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'school',
        'school_name_ar',
        'school_name_en',
        'language',
        'timezone',
        'allow_parent_notifications',
        'created_at',
    )

    search_fields = (
        'school__name',
        'school_name_ar',
        'school_name_en',
    )

    list_filter = (
        'language',
        'allow_parent_notifications',
    )

@admin.register(User)
class CustomUserAdmin(UserAdmin):

    list_display = (
        'id',
        'username',
        'email',
        'role',
        'school',
        'academic_year',
        'is_staff',
        'is_active',
    )

    list_filter = (
        'role',
        'school',
        'is_staff',
        'is_active',
    )

    search_fields = (
        'username',
        'email',
        'phone',
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            'School Information',
            {
                'fields': (
                    'role',
                    'school',
                    'academic_year',
                    'phone',
                    'is_active_school_user',
                )
            },
        ),
    )

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'code',
        'school',
        'academic_year',
        'is_active'
    )

    list_filter = (
        'school',
        'academic_year',
        'is_active'
    )

    search_fields = (
        'name',
        'code'
    )


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'classroom',
        'school',
        'academic_year',
        'is_active'
    )

    list_filter = (
        'school',
        'academic_year',
        'classroom',
        'is_active'
    )

    search_fields = (
        'name',
        'code'
    )

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'code',
        'school',
        'is_active',
    )

    list_filter = (
        'school',
        'is_active',
    )

    search_fields = (
        'name',
        'code',
    )


@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = (
        'classroom',
        'subject',
        'school',
        'academic_year',
        'weekly_periods',
    )

    list_filter = (
        'school',
        'academic_year',
        'classroom',
        'subject',
    )

    search_fields = (
        'classroom__name',
        'subject__name',
        'subject__code',
    )

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        'employee_code',
        'full_name',
        'school',
        'academic_year',
        'phone',
        'specialization',
        'is_active',
    )

    list_filter = (
        'school',
        'academic_year',
        'is_active',
    )

    search_fields = (
        'employee_code',
        'full_name',
        'phone',
        'email',
        'specialization',
    )

    readonly_fields = (
        'employee_code',
        'created_at',
    )

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = (
        'parent_code',
        'full_name',
        'school',
        'phone',
        'email',
        'is_active',
    )

    list_filter = (
        'school',
        'is_active',
    )

    search_fields = (
        'parent_code',
        'full_name',
        'phone',
        'email',
        'national_id',
    )

    readonly_fields = (
        'parent_code',
        'created_at',
    )

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'student_code',
        'full_name',
        'school',
        'gender',
        'current_classroom',
        'current_section',
        'is_active',
    )

    list_filter = (
        'school',
        'gender',
        'is_active',
    )

    search_fields = (
        'student_code',
        'full_name',
    )

    readonly_fields = (
        'student_code',
        'created_at',
    )

    def current_classroom(self, obj):
        enrollment = obj.current_enrollment
        return enrollment.classroom if enrollment else '-'

    def current_section(self, obj):
        enrollment = obj.current_enrollment
        return enrollment.section if enrollment else '-'


@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'school',
        'academic_year',
        'classroom',
        'section',
        'status',
        'is_current',
        'start_date',
        'end_date',
    )

    list_filter = (
        'school',
        'academic_year',
        'classroom',
        'section',
        'status',
        'is_current',
    )

    search_fields = (
        'student__full_name',
        'student__student_code',
    )

@admin.register(StudentGuardian)
class StudentGuardianAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'parent',
        'relationship',
        'is_primary',
        'can_receive_notifications',
        'can_receive_financial_alerts',
    )

    list_filter = (
        'relationship',
        'is_primary',
        'can_receive_notifications',
        'can_receive_financial_alerts',
    )

    search_fields = (
        'student__full_name',
        'student__student_code',
        'parent__full_name',
        'parent__parent_code',
    )

@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        'teacher',
        'subject',
        'classroom',
        'section',
        'school',
        'academic_year',
        'is_current',
    )

    list_filter = (
        'school',
        'academic_year',
        'classroom',
        'section',
        'subject',
        'is_current',
    )

    search_fields = (
        'teacher__full_name',
        'teacher__employee_code',
        'subject__name',
        'classroom__name',
        'section__name',
    )

@admin.register(AcademicTerm)
class AcademicTermAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'term_type',
        'school',
        'academic_year',
        'start_date',
        'end_date',
        'is_active',
    )

    list_filter = (
        'school',
        'academic_year',
        'term_type',
        'is_active',
    )

    search_fields = (
        'name',
    )

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'student_enrollment',
        'attendance_date',
        'status',
        'academic_term',
        'teacher_assignment',
        'created_at',
    )

    list_filter = (
        'attendance_date',
        'status',
        'academic_term',
        'teacher_assignment',
    )

    search_fields = (
        'student_enrollment__student__full_name',
        'student_enrollment__student__student_code',
    )

    readonly_fields = (
        'created_at',
    )
@admin.register(ExamType)
class ExamTypeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'code',
        'school',
        'max_score',
        'weight_percentage',
        'is_active',
      
    )

    list_filter = (
        'school',
        'is_active',
    )

    search_fields = (
        'name',
        'code',
    )

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'exam_type',
        'teacher_assignment',
        'academic_term',
        'exam_date',
        'total_marks',
        'status',
        'created_by',
    )

    list_filter = (
        'school',
        'academic_year',
        'academic_term',
        'exam_type',
        'status',
    )

    search_fields = (
        'title',
        'teacher_assignment__teacher__full_name',
        'teacher_assignment__subject__name',
    )

    readonly_fields = (
        'created_at',
        'created_at',

    )

@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = (
        'exam',
        'student_enrollment',
        'score',
        'status',
        'graded_by',
        'graded_at',
        'approved_by',
        'approved_at',
    )

    list_filter = (
        'exam',
        'status',
        'graded_by',
        'approved_by',
    )

    search_fields = (
        'exam__title',
        'student_enrollment__student__full_name',
        'student_enrollment__student__student_code',
    )

    readonly_fields = (
        'graded_at',
        'approved_at',
        'created_at',
    )

@admin.register(ExamResultLog)
class ExamResultLogAdmin(admin.ModelAdmin):
    list_display = (
        'exam_result',
        'old_score',
        'new_score',
        'old_status',
        'new_status',
        'changed_by',
        'changed_at',
    )

    list_filter = (
        'old_status',
        'new_status',
        'changed_by',
        'changed_at',
    )

    search_fields = (
        'exam_result__exam__title',
        'exam_result__student_enrollment__student__full_name',
        'reason',
    )

    readonly_fields = (
        'exam_result',
        'old_score',
        'new_score',
        'old_status',
        'new_status',
        'changed_by',
        'reason',
        'changed_at',
    )

    ordering = (
        '-changed_at',
    )