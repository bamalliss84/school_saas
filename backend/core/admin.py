from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.db import transaction
from django.http import HttpResponseRedirect
from django.db.models import Count, Prefetch, Q
from .models import School, AcademicYear, SchoolSetting, User
from django.contrib.auth.admin import UserAdmin
from .models import Classroom, Section, Subject, ClassSubject, Teacher, Parent, Student, StudentEnrollment
from .models import StudentGuardian, TeacherAssignment,AcademicTerm,Attendance,ExamType,Exam,ExamResult
from .models import ExamResultLog
from .models import (
    Homework, HomeworkActionLog, HomeworkAttachment, HomeworkSubmission,
    SchoolMembership,
    HomeworkSubmissionAttachment,
)
from rest_framework.exceptions import (
    PermissionDenied as DRFPermissionDenied, ValidationError as DRFValidationError,
)

from .services.exam_results import (
    create_exam_result, publish_results_bulk, unpublish_results_bulk,
    update_exam_result,
)
from .services.homework import (
    bulk_close_homework, bulk_grade_submissions, bulk_publish_homework,
    return_submission,
)
from .services.identity import (
    set_current_student_enrollment, sync_parent_memberships,
    sync_student_memberships, sync_teacher_memberships,
)


admin.site.site_header = 'نظام إدارة المدارس'
admin.site.site_title = 'إدارة School SaaS'
admin.site.index_title = 'لوحة إدارة المدرسة'


def _admin_has_permission(request):
    user = request.user
    return bool(
        user.is_active
        and user.is_staff
        and (
            user.is_superuser
            or user.role in ('super_admin', 'school_admin')
        )
    )


admin.site.has_permission = _admin_has_permission


class TenantAdminMixin:
    list_per_page = 50
    empty_value_display = '-'

    tenant_lookups = {
        'core.school': 'pk',
        'core.studentguardian': 'student__school_id',
        'core.attendance': 'student_enrollment__school_id',
        'core.examresult': 'exam__school_id',
        'core.examresultlog': 'exam_result__exam__school_id',
        'core.homeworksubmission': 'homework__school_id',
        'core.homeworkattachment': 'homework__school_id',
        'core.homeworksubmissionattachment': 'submission__homework__school_id',
        'core.homeworkactionlog': 'school_id',
    }

    def _is_global_admin(self, request):
        return request.user.is_superuser or request.user.role == 'super_admin'

    def _school_id(self, request):
        return request.user.school_id

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if self._is_global_admin(request):
            return queryset
        if request.user.role != 'school_admin' or not self._school_id(request):
            return queryset.none()
        label = self.model._meta.label_lower
        lookup = self.tenant_lookups.get(label)
        if lookup is None and any(
            field.name == 'school' for field in self.model._meta.fields
        ):
            lookup = 'school_id'
        return queryset.filter(**{lookup: self._school_id(request)}) if lookup else queryset.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not self._is_global_admin(request) and self._school_id(request):
            related = db_field.remote_field.model
            label = related._meta.label_lower
            if label == 'core.school':
                kwargs['queryset'] = related.objects.filter(pk=self._school_id(request))
            elif any(field.name == 'school' for field in related._meta.fields):
                kwargs['queryset'] = related.objects.filter(school_id=self._school_id(request))
            elif label == 'core.examresult':
                kwargs['queryset'] = related.objects.filter(exam__school_id=self._school_id(request))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not self._is_global_admin(request):
            if request.user.role != 'school_admin' or not self._school_id(request):
                raise PermissionDenied
            if obj._meta.label_lower == 'core.school':
                if not change or obj.pk != self._school_id(request):
                    raise PermissionDenied
            elif hasattr(obj, 'school_id'):
                if obj.school_id and obj.school_id != self._school_id(request):
                    raise PermissionDenied
                obj.school_id = self._school_id(request)
        obj.full_clean()
        super().save_model(request, obj, form, change)

    def _safe_admin_mutation(self, request, callback):
        try:
            return callback()
        except (DjangoValidationError, DRFValidationError, DRFPermissionDenied, PermissionDenied) as exc:
            self.message_user(request, str(exc), messages.ERROR)
            return HttpResponseRedirect(request.path)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        return self._safe_admin_mutation(
            request,
            lambda: super(TenantAdminMixin, self).changeform_view(
                request, object_id, form_url, extra_context,
            ),
        )

    def delete_view(self, request, object_id, extra_context=None):
        return self._safe_admin_mutation(
            request,
            lambda: super(TenantAdminMixin, self).delete_view(
                request, object_id, extra_context,
            ),
        )
    def has_add_permission(self, request):
        if (
            self.model._meta.label_lower == 'core.school'
            and not self._is_global_admin(request)
        ):
            return False
        return super().has_add_permission(request)

@admin.register(School)
class SchoolAdmin(TenantAdminMixin, admin.ModelAdmin):
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
class AcademicYearAdmin(TenantAdminMixin, admin.ModelAdmin):
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
class SchoolSettingAdmin(TenantAdminMixin, admin.ModelAdmin):
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
class CustomUserAdmin(TenantAdminMixin, UserAdmin):

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

    def save_model(self, request, obj, form, change):
        if not self._is_global_admin(request):
            if obj.is_superuser or obj.role == 'super_admin':
                raise PermissionDenied
        super().save_model(request, obj, form, change)

    fieldsets = UserAdmin.fieldsets + (        (
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
class ClassroomAdmin(TenantAdminMixin, admin.ModelAdmin):
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
class SectionAdmin(TenantAdminMixin, admin.ModelAdmin):
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
class SubjectAdmin(TenantAdminMixin, admin.ModelAdmin):
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
class ClassSubjectAdmin(TenantAdminMixin, admin.ModelAdmin):
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
class TeacherAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = (
        'employee_code',
        'full_name',
        'school',
        'academic_year',
        'active_membership_schools',
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
    def get_queryset(self, request):
        memberships = SchoolMembership.objects.filter(
            role='teacher', status='active',
        ).select_related('school')
        return super().get_queryset(request).prefetch_related(
            Prefetch('user__school_memberships', queryset=memberships, to_attr='_admin_teacher_memberships'),
        )

    @admin.display(description='Active schools')
    def active_membership_schools(self, obj):
        if not obj.user_id:
            return '-'
        return ', '.join(item.school.name for item in obj.user._admin_teacher_memberships) or '-'

@admin.register(Parent)
class ParentAdmin(TenantAdminMixin, admin.ModelAdmin):
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
class StudentAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = (
        'student_code',
        'full_name',
        'school',
        'current_school',
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
        'phone',
    )

    readonly_fields = (
        'student_code',
        'created_at',
    )

    def get_queryset(self, request):
        current = StudentEnrollment.objects.filter(
            status='active', is_current=True,
        ).select_related('classroom', 'section')
        return super().get_queryset(request).prefetch_related(
            Prefetch('enrollments', queryset=current, to_attr='_admin_current'),
        )

    def _current_enrollment(self, obj):
        return obj._admin_current[0] if obj._admin_current else None


    @admin.display(description='Current school')
    def current_school(self, obj):
        enrollment = self._current_enrollment(obj)
        return enrollment.school if enrollment else '-'

    def current_classroom(self, obj):
        enrollment = self._current_enrollment(obj)
        return enrollment.classroom if enrollment else '-'

    def current_section(self, obj):
        enrollment = self._current_enrollment(obj)
        return enrollment.section if enrollment else '-'


@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(TenantAdminMixin, admin.ModelAdmin):
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
    readonly_fields = ('is_current',)

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
            if obj.is_current:
                set_current_student_enrollment(obj)
            else:
                sync_student_memberships(obj.student)
        except Exception as exc:
            self.message_user(request, str(exc), messages.ERROR)
            raise

@admin.register(StudentGuardian)
class StudentGuardianAdmin(TenantAdminMixin, admin.ModelAdmin):
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

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
            sync_parent_memberships(parent=obj.parent)
        except Exception as exc:
            self.message_user(request, str(exc), messages.ERROR)
            raise

    def delete_model(self, request, obj):
        parent = obj.parent
        super().delete_model(request, obj)
        sync_parent_memberships(parent=parent)

    def delete_queryset(self, request, queryset):
        parents = list({item.parent for item in queryset.select_related('parent')})
        super().delete_queryset(request, queryset)
        for parent in parents:
            sync_parent_memberships(parent=parent)

@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(TenantAdminMixin, admin.ModelAdmin):
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

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
            sync_teacher_memberships(obj.teacher)
        except Exception as exc:
            self.message_user(request, str(exc), messages.ERROR)
            raise

@admin.register(AcademicTerm)
class AcademicTermAdmin(TenantAdminMixin, admin.ModelAdmin):
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
class AttendanceAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = (
        'student_name', 'attendance_date', 'status', 'school_name',
        'academic_year_name', 'classroom_name', 'section_name',
        'academic_term', 'teacher_assignment', 'created_at',
    )
    list_filter = (
        'attendance_date', 'status', 'student_enrollment__school',
        'student_enrollment__academic_year',
        'student_enrollment__classroom', 'student_enrollment__section',
        'academic_term', 'teacher_assignment',
    )
    search_fields = (
        'student_enrollment__student__full_name',
        'student_enrollment__student__student_code',
    )
    readonly_fields = ('created_at',)
    date_hierarchy = 'attendance_date'
    list_select_related = (
        'student_enrollment__student', 'student_enrollment__school',
        'student_enrollment__academic_year',
        'student_enrollment__classroom', 'student_enrollment__section',
        'academic_term', 'teacher_assignment',
    )

    @admin.display(description='الطالب', ordering='student_enrollment__student__full_name')
    def student_name(self, obj):
        return obj.student_enrollment.student.full_name

    @admin.display(description='المدرسة')
    def school_name(self, obj):
        return obj.student_enrollment.school

    @admin.display(description='السنة')
    def academic_year_name(self, obj):
        return obj.student_enrollment.academic_year

    @admin.display(description='الصف')
    def classroom_name(self, obj):
        return obj.student_enrollment.classroom

    @admin.display(description='الشعبة')
    def section_name(self, obj):
        return obj.student_enrollment.section

@admin.register(ExamType)
class ExamTypeAdmin(TenantAdminMixin, admin.ModelAdmin):
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
class ExamAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = (
        'title', 'exam_type', 'teacher_assignment', 'academic_term',
        'exam_date', 'total_marks', 'status', 'published_results_count',
        'created_by',
    )
    list_filter = (
        'school', 'academic_year', 'academic_term', 'exam_type', 'status',
    )
    search_fields = (
        'title', 'teacher_assignment__teacher__full_name',
        'teacher_assignment__subject__name',
    )
    readonly_fields = ('created_at',)
    actions = ('publish_selected_results', 'unpublish_selected_results')
    date_hierarchy = 'exam_date'
    list_select_related = (
        'school', 'academic_year', 'academic_term', 'exam_type',
        'teacher_assignment', 'created_by',
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            published_results_total=Count(
                'results', filter=Q(results__is_published=True), distinct=True,
            ),
        )

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not (
            request.user.is_superuser
            or request.user.role in ('super_admin', 'school_admin')
        ):
            actions.pop('publish_selected_results', None)
            actions.pop('unpublish_selected_results', None)
        return actions

    @admin.display(description='Published results', ordering='published_results_total')
    def published_results_count(self, obj):
        return obj.published_results_total

    def _scoped_action_exams(self, request, queryset):
        if not (
            request.user.is_superuser
            or request.user.role in ('super_admin', 'school_admin')
        ):
            raise DRFPermissionDenied('You cannot manage result publication.')
        exams = list(self.get_queryset(request).filter(pk__in=queryset.values('pk')))
        if not exams:
            raise DRFPermissionDenied('No permitted exams were selected.')
        return exams

    @admin.action(description='Publish all approved results for selected exams')
    def publish_selected_results(self, request, queryset):
        try:
            summaries = publish_results_bulk(
                exams=self._scoped_action_exams(request, queryset),
                changed_by=request.user,
                reason='Published through Django Admin.', request=request,
            )
        except (DRFValidationError, DRFPermissionDenied) as exc:
            messages.error(request, str(exc.detail))
            return
        published_count = sum(item['published_count'] for item in summaries)
        messages.success(
            request, f'Published {published_count} result(s).',
        )

    @admin.action(description='Unpublish results for selected exams')
    def unpublish_selected_results(self, request, queryset):
        try:
            summaries = unpublish_results_bulk(
                exams=self._scoped_action_exams(request, queryset),
                changed_by=request.user,
                reason='Unpublished through Django Admin.', request=request,
            )
        except (DRFValidationError, DRFPermissionDenied) as exc:
            messages.error(request, str(exc.detail))
            return
        unpublished_count = sum(item['unpublished_count'] for item in summaries)
        messages.success(
            request, f'Unpublished {unpublished_count} result(s).',
        )

@admin.register(ExamResult)
class ExamResultAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = (
        'exam', 'student_enrollment', 'score', 'status', 'workflow_status',
        'graded_by', 'graded_at', 'approved_by', 'approved_at',
        'is_published', 'published_by', 'published_at',
    )
    list_filter = (
        'workflow_status', 'status', 'exam__school', 'exam__academic_year',
        'exam__academic_term', 'exam__teacher_assignment__subject',
    )
    search_fields = (
        'exam__title', 'student_enrollment__student__full_name',
        'student_enrollment__student__student_code',
    )
    readonly_fields = (
        'workflow_status', 'approval_reason', 'graded_by', 'graded_at',
        'approved_by', 'approved_at', 'is_published', 'published_by',
        'published_at', 'created_at',
    )
    list_select_related = (
        'exam', 'exam__school', 'exam__academic_year', 'exam__academic_term',
        'exam__teacher_assignment__subject', 'student_enrollment__student',
        'graded_by', 'approved_by', 'published_by',
    )

    def save_model(self, request, obj, form, change):
        if change:
            previous = ExamResult.objects.get(pk=obj.pk)
            saved = update_exam_result(
                exam_result=previous,
                changed_by=request.user,
                request=request,
                reason='Changed through Django Admin.',
                score=obj.score,
                status=obj.status,
                remarks=obj.remarks,
            )
        else:
            saved = create_exam_result(
                exam=obj.exam,
                student_enrollment=obj.student_enrollment,
                changed_by=request.user,
                request=request,
                score=obj.score,
                status=obj.status,
                remarks=obj.remarks,
            )
        obj.pk = saved.pk
        obj._state.adding = False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ExamResultLog)
class ExamResultLogAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = (
        'exam_result', 'action', 'old_score', 'new_score', 'old_status',
        'new_status', 'old_workflow_status', 'new_workflow_status',
        'old_is_published', 'new_is_published', 'published_by',
        'changed_by', 'changed_at',
    )
    list_filter = (
        'action', 'old_status', 'new_status', 'old_workflow_status',
        'new_workflow_status', 'changed_by', 'changed_at',
    )
    search_fields = (
        'exam_result__exam__title',
        'exam_result__student_enrollment__student__full_name',
        'reason', 'request_id',
    )
    readonly_fields = (
        'exam_result', 'old_score', 'new_score', 'old_status', 'new_status',
        'old_workflow_status', 'new_workflow_status', 'old_approval_reason',
        'new_approval_reason', 'old_is_published', 'new_is_published',
        'published_by', 'action', 'changed_by', 'reason', 'request_id',
        'ip_address', 'user_agent', 'changed_at',
    )
    list_select_related = (
        'exam_result__exam', 'exam_result__student_enrollment__student',
        'changed_by', 'published_by',
    )
    ordering = ('-changed_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
@admin.register(Homework)
class HomeworkAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = (
        'title', 'school', 'academic_year', 'academic_term', 'teacher_assignment',
        'status', 'due_date', 'submission_count', 'attachment_count',
    )
    list_filter = ('status', 'school', 'academic_year', 'academic_term')
    search_fields = ('title', 'description', 'teacher_assignment__teacher__full_name')
    date_hierarchy = 'created_at'
    list_select_related = (
        'school', 'academic_year', 'academic_term', 'teacher_assignment__teacher',
        'teacher_assignment__subject',
    )
    actions = ('publish_selected', 'close_selected')

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _submission_count=Count('submissions', distinct=True),
            _attachment_count=Count('attachments', distinct=True),
        )

    @admin.display(ordering='_submission_count')
    def submission_count(self, obj):
        return obj._submission_count

    @admin.display(ordering='_attachment_count')
    def attachment_count(self, obj):
        return obj._attachment_count

    @admin.action(description='Publish selected homework')
    def publish_selected(self, request, queryset):
        try:
            with transaction.atomic():
                saved = bulk_publish_homework(
                    homework_items=list(queryset.order_by('pk')),
                    actor=request.user, request=request,
                )
            self.message_user(request, f'Published {len(saved)} homework item(s).', messages.SUCCESS)
        except (DRFValidationError, DRFPermissionDenied, PermissionDenied) as exc:
            self.message_user(request, str(exc), messages.ERROR)

    @admin.action(description='Close selected homework')
    def close_selected(self, request, queryset):
        try:
            with transaction.atomic():
                saved = bulk_close_homework(
                    homework_items=list(queryset.order_by('pk')),
                    actor=request.user, request=request,
                )
            self.message_user(request, f'Closed {len(saved)} homework item(s).', messages.SUCCESS)
        except (DRFValidationError, DRFPermissionDenied, PermissionDenied) as exc:
            self.message_user(request, str(exc), messages.ERROR)


@admin.register(HomeworkAttachment)
class HomeworkAttachmentAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('original_name', 'homework', 'content_type', 'file_size', 'uploaded_by', 'created_at')
    list_filter = ('content_type', 'created_at')
    search_fields = ('original_name', 'homework__title')
    list_select_related = ('homework__school', 'uploaded_by')
    readonly_fields = ('original_name', 'content_type', 'file_size', 'uploaded_by', 'created_at')



class HomeworkSubmissionActionForm(ActionForm):
    grade = forms.DecimalField(required=False, min_value=0, decimal_places=2)
    teacher_note = forms.CharField(required=False)
@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = (
        'student_name', 'student_code', 'homework', 'status', 'grade',
        'submitted_at', 'graded_at',
    )
    list_filter = ('status', 'homework__school', 'homework__academic_year')
    search_fields = (
        'student_enrollment__student__full_name',
        'student_enrollment__student__student_code', 'homework__title',
    )
    list_select_related = (
        'homework__school', 'student_enrollment__student', 'graded_by',
    )
    actions = ('grade_selected', 'return_selected')
    action_form = HomeworkSubmissionActionForm
    readonly_fields = (
        'answer', 'status', 'submitted_at', 'grade', 'teacher_note',
        'graded_by', 'graded_at', 'returned_at', 'created_at', 'updated_at',
    )

    @admin.display(ordering='student_enrollment__student__full_name')
    def student_name(self, obj):
        return obj.student_enrollment.student.full_name

    @admin.display(ordering='student_enrollment__student__student_code')
    def student_code(self, obj):
        return obj.student_enrollment.student.student_code


    @admin.action(description='Grade selected submissions')
    def grade_selected(self, request, queryset):
        grade = request.POST.get('grade')
        if grade in (None, ''):
            self.message_user(request, 'A grade is required.', messages.ERROR)
            return
        try:
            with transaction.atomic():
                saved = bulk_grade_submissions(
                    items=[{
                        'submission': item,
                        'grade': forms.DecimalField().clean(grade),
                        'teacher_note': request.POST.get('teacher_note', ''),
                    } for item in queryset.order_by('pk')],
                    actor=request.user,
                    request=request,
                )
            self.message_user(request, f'Graded {len(saved)} submission(s).', messages.SUCCESS)
        except (forms.ValidationError, DRFValidationError, DRFPermissionDenied, PermissionDenied) as exc:
            self.message_user(request, str(exc), messages.ERROR)

    @admin.action(description='Return selected submissions')
    def return_selected(self, request, queryset):
        try:
            with transaction.atomic():
                saved = [return_submission(
                    submission=item, actor=request.user, request=request,
                ) for item in queryset.order_by('pk')]
            self.message_user(request, f'Returned {len(saved)} submission(s).', messages.SUCCESS)
        except (DRFValidationError, DRFPermissionDenied, PermissionDenied) as exc:
            self.message_user(request, str(exc), messages.ERROR)


@admin.register(HomeworkSubmissionAttachment)
class HomeworkSubmissionAttachmentAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('original_name', 'submission', 'content_type', 'file_size', 'uploaded_by', 'created_at')
    list_filter = ('content_type', 'created_at')
    search_fields = ('original_name', 'submission__homework__title')
    list_select_related = ('submission__homework__school', 'uploaded_by')
    readonly_fields = ('original_name', 'content_type', 'file_size', 'uploaded_by', 'created_at')


@admin.register(HomeworkActionLog)
class HomeworkActionLogAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('entity_type', 'entity_id', 'action', 'school', 'actor', 'created_at')
    list_filter = ('entity_type', 'action', 'school', 'created_at')
    search_fields = ('entity_type', 'entity_id', 'request_id')
    list_select_related = ('school', 'actor')
    readonly_fields = (
        'school', 'actor', 'action', 'entity_type', 'entity_id', 'old_data',
        'new_data', 'reason', 'request_id', 'ip_address', 'user_agent', 'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
@admin.register(SchoolMembership)
class SchoolMembershipAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = (
        'user', 'school', 'role', 'status', 'is_default', 'start_date',
        'end_date', 'last_used_at',
    )
    list_filter = ('school', 'role', 'status', 'is_default')
    search_fields = ('user__username', 'user__email', 'school__name', 'school__code')
    list_select_related = ('user', 'school')
    date_hierarchy = 'created_at'

    def save_model(self, request, obj, form, change):
        if not self._is_global_admin(request):
            if request.user.role != 'school_admin' or obj.school_id != request.user.school_id:
                raise PermissionDenied
            if obj.role == 'super_admin':
                raise PermissionDenied
        super().save_model(request, obj, form, change)