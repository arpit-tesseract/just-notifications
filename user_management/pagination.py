from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class UserManagementPagination(PageNumberPagination):
    page_size = 10                          # Default number of items per page
    page_size_query_param = 'page_size'     # Lets client change page size (e.g., ?page_size=50)
    max_page_size = 100                     # Max items client can request
    
    # This is the method override
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,  # <-- This is the new key
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })