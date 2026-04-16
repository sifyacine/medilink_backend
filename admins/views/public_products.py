"""
Public product catalog views for the Medilink platform.

These endpoints are read-only and intended for public users who want to
browse available products and contact Medilink to place an order.
No cart or checkout flow is provided here.
"""
from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny

from admins.models.products import MediLinkProduct
from admins.serializers.public_products import (
    PublicProductListSerializer,
    PublicProductDetailSerializer,
)


class PublicProductPagination(PageNumberPagination):
    """Pagination for public product catalog endpoints."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class PublicProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only public catalog for MediLink products.

    Supported query params:
    - search: search by name, sku, brand, manufacturer, description, category
    - category: filter by category
    - is_active: filter active/inactive products (defaults to active only)
    - ordering: order by name, selling_price, rating, stock_quantity, created_at
    - page: pagination page number
    - page_size: number of items per page (max 100)
    """
    permission_classes = [AllowAny]
    pagination_class = PublicProductPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'sku', 'brand', 'manufacturer', 'description', 'category']
    ordering_fields = ['name', 'selling_price', 'rating', 'stock_quantity', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = MediLinkProduct.objects.select_related('added_by', 'updated_by').prefetch_related('gallery_images')
        queryset = queryset.filter(is_active=True)

        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PublicProductDetailSerializer
        return PublicProductListSerializer
