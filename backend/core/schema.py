from django.conf import settings
from rest_framework.permissions import BasePermission
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

class MembershipJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = 'core.context.MembershipJWTAuthentication'
    name = 'jwtAuth'

    def get_security_definition(self, auto_schema):
        return {'type': 'http', 'scheme': 'bearer', 'bearerFormat': 'JWT'}

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

def add_school_context_header(result, generator, request, public):
    """Document the explicit tenant selector on canonical authenticated APIs."""
    parameter = {
        'name': 'X-School-Membership-ID', 'in': 'header', 'required': False,
        'schema': {'type': 'integer', 'minimum': 1},
        'description': ('Selects an owned school membership. Required with multiple '
                        'active contexts; historical contexts are read-only.'),
    }
    excluded = ('/api/v1/auth/login/', '/api/v1/auth/refresh/')
    for path, path_item in result.get('paths', {}).items():
        if not path.startswith('/api/v1/') or path in excluded:
            continue
        for method, operation in path_item.items():
            if method.lower() not in {'get', 'post', 'put', 'patch', 'delete'}:
                continue
            parameters = operation.setdefault('parameters', [])
            if not any(item.get('name') == parameter['name'] for item in parameters):
                parameters.append(parameter.copy())
    return result