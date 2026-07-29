class SchoolQuerySetMixin:
    """Restrict querysets to the authenticated user's school."""

    school_lookup = "school_id"

    def get_school_queryset(self, queryset):
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        if user.role == 'super_admin':
            return queryset

        if not user.school_id:
            return queryset.none()

        if queryset.model._meta.label_lower == 'core.school':
            return queryset.filter(pk=user.school_id)

        return queryset.filter(**{self.school_lookup: user.school_id})
