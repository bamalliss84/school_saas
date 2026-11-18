from .context import request_role, request_school


class SchoolQuerySetMixin:
    """Restrict querysets to the school of the selected context.

    A super_admin without a selected school is platform-wide; with one, scoped to it.
    """

    school_lookup = "school_id"

    def get_school_queryset(self, queryset):
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        school = request_school(self.request)
        if school is None:
            return queryset if request_role(self.request) == 'super_admin' else queryset.none()

        if queryset.model._meta.label_lower == 'core.school':
            return queryset.filter(pk=school.pk)

        return queryset.filter(**{self.school_lookup: school.pk})
