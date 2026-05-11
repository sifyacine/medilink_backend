from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class BaseModelViewSet(viewsets.ModelViewSet):
    """
    Base viewset that enforces StandardPagination on all list endpoints.
    Inherit from this instead of viewsets.ModelViewSet to ensure pagination
    cannot be accidentally omitted.
    """
    pagination_class = StandardPagination
