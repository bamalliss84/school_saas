from django.db.models import Q
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied

from .context import require_writable_context
from .models import Parent, Student, StudentGuardian
from .pagination import StandardResultsSetPagination
from .parent_admin_serializers import (
    GuardianAdminSerializer, GuardianWriteSerializer, ParentAdminSerializer,
)
from .permissions import IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin
from .services.identity import delete_guardian_link


def parents_visible_to_school(school, academic_year=None):
    """Return parents operationally visible in the active tenant context.

    A guardian link from a historical enrollment must not make a parent visible
    in the current school/year administration surface.
    """
    linked = Q(
        students__student__enrollments__school=school,
        students__student__enrollments__is_current=True,
        students__student__enrollments__status='active',
    )
    if academic_year is not None:
        linked &= Q(students__student__enrollments__academic_year=academic_year)
    return Parent.objects.filter(Q(school=school) | linked).distinct()


def student_visible_to_school(student_id, school, *, current_for_write=False):
    filters = {'pk': student_id, 'enrollments__school': school}
    if current_for_write:
        filters.update({'enrollments__is_current': True, 'enrollments__status': 'active'})
    return Student.objects.filter(**filters).distinct().first()


class ParentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ParentAdminSerializer
    permission_classes = (IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        school = getattr(self.request, 'active_school', None)
        if not school:
            return Parent.objects.none()
        queryset = parents_visible_to_school(school, getattr(self.request, 'active_academic_year', None)).select_related('school', 'user')
        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) | Q(parent_code__icontains=search)
                | Q(phone__icontains=search) | Q(email__icontains=search)
            )
        if 'is_active' in self.request.query_params:
            queryset = queryset.filter(is_active=self.request.query_params['is_active'].lower() == 'true')
        return queryset.order_by('full_name', 'id')

    def perform_create(self, serializer):
        require_writable_context(self.request)
        serializer.save()


class ParentDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = ParentAdminSerializer
    permission_classes = (IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin)

    def get_queryset(self):
        school = getattr(self.request, 'active_school', None)
        return parents_visible_to_school(school, getattr(self.request, 'active_academic_year', None)).select_related('school', 'user') if school else Parent.objects.none()

    def perform_update(self, serializer):
        require_writable_context(self.request)
        if serializer.instance.school_id != self.request.active_school.pk:
            raise PermissionDenied('Only the profile-owning school can update this parent.')
        serializer.save()


class GuardianListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = (IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin)
    pagination_class = StandardResultsSetPagination

    def get_student(self, write=False):
        student = student_visible_to_school(
            self.kwargs['student_id'], self.request.active_school, current_for_write=write,
        )
        if student is None:
            from rest_framework.exceptions import NotFound
            raise NotFound('Student was not found.')
        return student

    def get_queryset(self):
        return StudentGuardian.objects.filter(student=self.get_student()).select_related('parent', 'student').order_by('-is_primary', 'id')

    def get_serializer_class(self):
        return GuardianWriteSerializer if self.request.method == 'POST' else GuardianAdminSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['student'] = self.get_student(write=self.request.method == 'POST')
        return context

    def perform_create(self, serializer):
        require_writable_context(self.request)
        serializer.save()


class GuardianDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin)

    def get_student(self):
        student = student_visible_to_school(
            self.kwargs['student_id'], self.request.active_school,
            current_for_write=self.request.method in ('PUT', 'PATCH', 'DELETE'),
        )
        if student is None:
            from rest_framework.exceptions import NotFound
            raise NotFound('Student was not found.')
        return student

    def get_queryset(self):
        return StudentGuardian.objects.filter(student=self.get_student()).select_related('parent', 'student')

    def get_serializer_class(self):
        return GuardianAdminSerializer if self.request.method == 'GET' else GuardianWriteSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context(); context['student'] = self.get_student(); return context

    def perform_update(self, serializer):
        require_writable_context(self.request); serializer.save()

    def perform_destroy(self, instance):
        require_writable_context(self.request)
        delete_guardian_link(guardian=instance, school=self.request.active_school)
