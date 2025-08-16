import django_filters
from accounts.models import User

class UserFilter(django_filters.FilterSet):
    department = django_filters.CharFilter(field_name='department__name', lookup_expr='icontains')
    level = django_filters.NumberFilter(field_name='level')
    status = django_filters.CharFilter(method='filter_by_status')

    class Meta:
        model = User
        fields = ['department', 'level', 'status','gender']

    def filter_by_status(self, queryset, name, value):
        status_value = value.lower()
        filtered_users = [u.id for u in queryset if u.status.lower() == status_value]
        return queryset.filter(id__in=filtered_users)
