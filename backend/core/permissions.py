from rest_framework.permissions import BasePermission


def _request_role(request):
    """Return the canonical request role, with legacy fallback only for old paths."""
    return getattr(request, 'active_role', None) or getattr(request.user, 'role', None)


class IsActiveSchoolUser(BasePermission):
    """Reject stale tokens and unavailable active tenant contexts."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if not user.is_active or not user.is_active_school_user:
            return False

        role = _request_role(request)
        if role == 'super_admin':
            return True

        membership = getattr(request, 'active_membership', None)
        school = getattr(request, 'active_school', None)
        if membership is not None:
            return bool(
                membership.status in ('active', 'historical')
                and school
                and school.is_active
            )

        # Temporary fallback for legacy endpoints that don't yet resolve an
        # explicit membership context. New APIs must use request.active_*.
        return bool(user.school_id and user.school.is_active)


class RolePermission(BasePermission):
    allowed_roles = ()

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and _request_role(request) in self.allowed_roles
        )


class IsSuperAdmin(RolePermission):
    allowed_roles = ('super_admin',)


class IsSchoolAdmin(RolePermission):
    allowed_roles = ('school_admin',)


class IsSchoolAdminOrSuperAdmin(RolePermission):
    allowed_roles = ('super_admin', 'school_admin')


class IsTeacher(RolePermission):
    allowed_roles = ('teacher',)


class IsParent(RolePermission):
    allowed_roles = ('parent',)


class IsStudent(RolePermission):
    allowed_roles = ('student',)


class IsAttendanceManager(RolePermission):
    allowed_roles = ('super_admin', 'school_admin', 'teacher')
