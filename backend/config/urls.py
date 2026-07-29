from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core.health import LivenessAPIView, ReadinessAPIView
from core.schema import ProjectRedocView, ProjectSchemaAPIView, ProjectSwaggerView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', LivenessAPIView.as_view(), name='health'),
    path('health/live/', LivenessAPIView.as_view(), name='health-live'),
    path('health/ready/', ReadinessAPIView.as_view(), name='health-ready'),
    path('api/schema/', ProjectSchemaAPIView.as_view(), name='api-schema'),
    path('api/docs/', ProjectSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
    path('api/redoc/', ProjectRedocView.as_view(url_name='api-schema'), name='api-redoc'),
    path('api/v1/schema/', ProjectSchemaAPIView.as_view(), name='api-v1-schema'),
    path('api/v1/docs/', ProjectSwaggerView.as_view(url_name='api-v1-schema'), name='api-v1-docs'),
    path('api/v1/health/', LivenessAPIView.as_view(), name='api-v1-health'),
    path('api/v1/', include('config.api_urls')),
    # Temporary compatibility routes. New clients should use /api/v1/.
    path('api/', include('config.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)