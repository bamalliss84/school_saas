from django.conf import settings
from rest_framework.permissions import BasePermission
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


class CanViewAPIDocumentation(BasePermission):
    def has_permission(self, request, view):
        return settings.DEBUG or bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )


class ProjectSchemaAPIView(SpectacularAPIView):
    permission_classes = (CanViewAPIDocumentation,)
    throttle_scope = 'docs'
    urlconf = 'config.schema_urls'


class ProjectSwaggerView(SpectacularSwaggerView):
    permission_classes = (CanViewAPIDocumentation,)
    throttle_scope = 'docs'


class ProjectRedocView(SpectacularRedocView):
    permission_classes = (CanViewAPIDocumentation,)
    throttle_scope = 'docs'


def exclude_compatibility_paths(endpoints):
    """Keep legacy /api/ routes live while documenting canonical /api/v1/ only."""
    return [
        endpoint for endpoint in endpoints
        if not (
            endpoint[0].startswith('/api/')
            and not endpoint[0].startswith('/api/v1/')
        )
    ]