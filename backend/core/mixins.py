class SchoolQuerySetMixin:

    def get_school_queryset(self, queryset):
        user = self.request.user

        if user.role == 'super_admin':
            return queryset

        return queryset.filter(
            school=user.school
        )