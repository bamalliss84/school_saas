from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, NotFound, PermissionDenied
from rest_framework.permissions import SAFE_METHODS
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import AcademicYear, SchoolMembership, StudentEnrollment


class ContextRequired(APIException):
    status_code = 409
    default_detail = 'A school membership context is required.'
    default_code = 'context_required'
    context_error_code = 'context_required'


def get_user_memberships(user, *, include_ended=False):
    queryset = SchoolMembership.objects.filter(user=user).select_related('school')
    if not include_ended:
        queryset = queryset.exclude(status='ended')
    return queryset.order_by('-is_default', 'school__name', 'role', 'pk')


def user_has_membership(user, school, role, *, statuses=('active',)):
    return SchoolMembership.objects.filter(
        user=user, school=school, role=role, status__in=statuses,
    ).exists()


def ensure_legacy_membership(user):
    if user.role == 'super_admin' and not user.school_id:
        return None
    if not user.school_id:
        return None
    membership, _ = SchoolMembership.objects.get_or_create(
        user=user,
        school_id=user.school_id,
        role=user.role,
        defaults={'status': 'active', 'is_default': not user.school_memberships.exists()},
    )
    return membership


def _academic_year_for_membership(membership, request):
    requested = request.query_params.get('academic_year_id') if hasattr(request, 'query_params') else None
    years = AcademicYear.objects.filter(school_id=membership.school_id)
    if requested:
        try:
            return years.get(pk=int(requested))
        except (ValueError, AcademicYear.DoesNotExist) as exc:
            raise NotFound('Academic year was not found.') from exc
    if membership.role == 'student':
        enrollment = StudentEnrollment.objects.filter(
            student__user_id=membership.user_id,
            school_id=membership.school_id,
        ).select_related('academic_year').order_by('-is_current', '-academic_year__start_date').first()
        if enrollment:
            return enrollment.academic_year
    return years.filter(is_active=True).order_by('-start_date', '-pk').first()


def restore_legacy_user_context(user):
    """Restore the in-memory user after the request-local compatibility adapter."""
    if hasattr(user, '_legacy_school_id'):
        user.school_id = user._legacy_school_id
        user.role = user._legacy_role
        user.academic_year_id = user._legacy_academic_year_id


def apply_membership_context(request, user, membership):
    # Request-local compatibility adapter only. Never save this mutated user:
    # canonical persistence must use sync_legacy_user_context with real records.
    request.active_membership = membership
    request.active_school = membership.school
    request.active_role = membership.role
    request.active_academic_year = _academic_year_for_membership(membership, request)
    user._legacy_school_id = user.school_id
    user._legacy_role = user.role
    user._legacy_academic_year_id = user.academic_year_id
    user.school = membership.school
    user.role = membership.role
    user.academic_year = request.active_academic_year
    user._active_membership = membership


def resolve_membership_context(request, user, *, optional=False):
    if not user.is_active or not user.is_active_school_user:
        raise PermissionDenied('This account is not available.')
    memberships = get_user_memberships(user, include_ended=True)
    if not memberships.exists():
        ensure_legacy_membership(user)
        memberships = get_user_memberships(user, include_ended=True)

    header = request.headers.get('X-School-Membership-ID')
    membership = None
    if header:
        try:
            membership_id = int(header)
        except ValueError as exc:
            raise NotFound('School context was not found.') from exc
        membership = memberships.filter(pk=membership_id).first()
        if membership is None:
            raise NotFound('School context was not found.')
    else:
        active = list(memberships.filter(status='active')[:2])
        if len(active) == 1:
            membership = active[0]
        elif len(active) > 1 and not optional:
            raise ContextRequired()
        elif optional:
            membership = memberships.filter(status='active', is_default=True).first()
            membership = membership or (active[0] if active else None)
        else:
            historical = list(memberships.filter(status='historical')[:2])
            if len(historical) == 1:
                membership = historical[0]
            elif historical:
                raise ContextRequired()

    if membership is None:
        if user.role == 'super_admin':
            request.active_membership = None
            request.active_school = None
            request.active_role = 'super_admin'
            request.active_academic_year = None
            return None
        if optional:
            return None
        raise PermissionDenied('No usable school context is available.')
    if membership.status in ('suspended', 'ended'):
        raise PermissionDenied('This school context is not available.')
    if not membership.school.is_active:
        raise PermissionDenied('This school context is not available.')
    if membership.status == 'historical' and request.method not in SAFE_METHODS:
        raise PermissionDenied('Historical school context is read-only.')
    apply_membership_context(request, user, membership)
    return membership


def get_active_membership(request):
    return getattr(request, 'active_membership', None)


def get_active_school(request):
    return getattr(request, 'active_school', None)


def get_active_role(request):
    return getattr(request, 'active_role', None)


def require_writable_context(request):
    membership = get_active_membership(request)
    if membership and membership.status == 'historical':
        raise PermissionDenied('Historical school context is read-only.')
    return membership


class MembershipJWTAuthentication(JWTAuthentication):
    optional_context_paths = (
        '/auth/contexts/', '/auth/context/default/', '/auth/logout/',
    )

    def authenticate(self, request):
        authenticated = super().authenticate(request)
        if authenticated is None:
            return None
        user, token = authenticated
        optional = (
            any(request.path.endswith(path) for path in self.optional_context_paths)
            or request.path.endswith('/students/me/schools/')
            or request.path.endswith('/students/me/academic-history/')
            or ('/parents/me/children/' in request.path and request.path.endswith('/schools/'))
            or ('/parents/me/children/' in request.path and request.path.endswith('/academic-history/'))
        )
        resolve_membership_context(request, user, optional=optional)
        return user, token