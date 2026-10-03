from rest_framework import generics

from .context import require_writable_context
from .models import StudentEnrollment
from .permissions import IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin
from .selectors import students_for_user
from .student_admin_serializers import StudentEnrollmentAdminSerializer


class StudentEnrollmentMixin:
    serializer_class = StudentEnrollmentAdminSerializer
    permission_classes = (IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin)

    def get_student(self):
        if not hasattr(self, '_student'):
            self._student = generics.get_object_or_404(
                students_for_user(self.request.user, request=self.request),
                pk=self.kwargs['student_id'],
            )
        return self._student

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return StudentEnrollment.objects.none()
        return StudentEnrollment.objects.filter(
            student=self.get_student(), school=getattr(self.request, 'active_school', None),
        ).select_related('academic_year', 'classroom', 'section').order_by(
            '-is_current', '-academic_year__start_date', '-created_at',
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['student'] = self.get_student()
        return context


class StudentEnrollmentListCreateAPIView(StudentEnrollmentMixin, generics.ListCreateAPIView):
    pagination_class = None

    def perform_create(self, serializer):
        require_writable_context(self.request)
        serializer.save()


class StudentEnrollmentDetailAPIView(StudentEnrollmentMixin, generics.RetrieveUpdateAPIView):
    def perform_update(self, serializer):
        require_writable_context(self.request)
        serializer.save()
