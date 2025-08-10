import django_filters
from .models.elections import Election

class ElectionFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(method='filter_status')
    department = django_filters.NumberFilter(field_name='department__id')
    title = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Election
        fields = ['status', 'department', 'title']

    def filter_status(self, queryset, name, value):
        """Filter elections by computed status."""
        status_map = {
            'upcoming': lambda e: e.get_status().lower() == 'upcoming',
            'ongoing': lambda e: e.get_status().lower() == 'ongoing',
            'ended': lambda e: e.get_status().lower() == 'ended',
            'suspended': lambda e: e.get_status().lower() == 'suspended',
            'cancelled': lambda e: e.get_status().lower() == 'cancelled',
        }
        status_filter = status_map.get(value.lower())
        if status_filter:
            return [e for e in queryset if status_filter(e)]
        return queryset
