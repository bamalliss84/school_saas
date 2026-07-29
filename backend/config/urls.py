from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from core.views import (
    CurrentUserAPIView,
    LoginTokenObtainPairView,
    LogoutAPIView,
    ParentChildrenAPIView,
    SchoolListAPIView,
    SecureTokenRefreshView,
    StudentAcademicHistoryAPIView,
    StudentDetailAPIView,
    StudentListAPIView,
    StudentMeProfileAPIView,
    TeacherAssignmentsAPIView,
    TeacherClassesAPIView,
    TeacherStudentsAPIView,
    TeacherSubjectsAPIView,
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/login/', LoginTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', SecureTokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/logout/', LogoutAPIView.as_view(), name='token_logout'),
    path('api/auth/me/', CurrentUserAPIView.as_view(), name='current-user'),
    path('api/schools/', SchoolListAPIView.as_view(), name='school-list'),
    path('api/students/', StudentListAPIView.as_view(), name='student-list'),
    path('api/students/me/profile/', StudentMeProfileAPIView.as_view(), name='student-me-profile'),
    path('api/students/<int:pk>/', StudentDetailAPIView.as_view(), name='student-detail'),
    path('api/students/<int:pk>/academic-history/', StudentAcademicHistoryAPIView.as_view(), name='student-academic-history'),
    path('api/parents/me/children/', ParentChildrenAPIView.as_view(), name='parent-children'),
    path('api/teachers/me/assignments/', TeacherAssignmentsAPIView.as_view(), name='teacher-assignments'),
    path('api/teachers/me/classes/', TeacherClassesAPIView.as_view(), name='teacher-classes'),
    path('api/teachers/me/students/', TeacherStudentsAPIView.as_view(), name='teacher-students'),
    path('api/teachers/me/subjects/', TeacherSubjectsAPIView.as_view(), name='teacher-subjects'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)