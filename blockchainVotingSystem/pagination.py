# accounts/pagination.py or core/pagination.py (depending on structure)

from collections import OrderedDict
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class PageNumberPaginationNoCount(PageNumberPagination):
    """Override get_paginated_response to remove 'count' from Response"""

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                ]
            )
        )
