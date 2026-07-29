from rest_framework.permissions import BasePermission


class IsActiveSchoolUser(BasePermission):
    """Reject stale access tokens when the account or tenant is disabled."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if not user.is_active or not user.is_active_school_user:
            return False
        if user.role == 'super_admin':
            return True
        return bool(user.school_id and user.school.is_active)


class RolePermission(BasePermission):
    allowed_roles = ()

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in self.allowed_roles
        )


class IsSuperAdmin(RolePermission):
    allowed_roles = ('super_admin',)


class IsSchoolAdmin(RolePermission):
    allowed_roles = ('school_admin',)


class IsTeacher(RolePermission):
    allowed_roles = ('teacher',)


class IsParent(RolePermission):
    allowed_roles = ('parent',)


class IsStudent(RolePermission):
    allowed_roles = ('student',)