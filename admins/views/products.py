"""
Admin views for MediLink platform products and income tracking.

Endpoints:
  GET    /api/admin/products/              List all products
  POST   /api/admin/products/              Create a product
  GET    /api/admin/products/{id}/         Product detail
  PATCH  /api/admin/products/{id}/         Update a product
  DELETE /api/admin/products/{id}/         Delete a product
  PATCH  /api/admin/products/{id}/toggle/  Toggle is_active status

  GET    /api/admin/income/                List all income / sales records
  POST   /api/admin/income/                Record a sale manually
  GET    /api/admin/income/{id}/           Sale detail
  GET    /api/admin/income/stats/          Aggregate income statistics
"""
from decimal import Decimal

from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from admins.models.products import MediLinkProduct, MediLinkSale, SaleStatus
from admins.permissions import IsAdmin, IsAdminOrSeller
from admins.serializers.products import (
    MediLinkProductSerializer,
    MediLinkProductListSerializer,
    MediLinkSaleSerializer,
)


class MediLinkProductViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for MediLink platform products.
    Only accessible by MediLink admins.
    """
    permission_classes = [IsAuthenticated, IsAdminOrSeller]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'sku', 'brand', 'manufacturer', 'description', 'category']
    ordering_fields = ['name', 'selling_price', 'cost_price', 'rating', 'stock_quantity', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = MediLinkProduct.objects.select_related('added_by', 'updated_by').prefetch_related('gallery_images')

        category = self.request.query_params.get('category')
        is_active = self.request.query_params.get('is_active')

        if category:
            qs = qs.filter(category=category)
        if is_active is not None:
            qs = qs.filter(is_active=(is_active.lower() == 'true'))

        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return MediLinkProductListSerializer
        return MediLinkProductSerializer

    @action(detail=True, methods=['patch'], url_path='toggle')
    def toggle_active(self, request, pk=None):
        """PATCH /api/admin/products/{id}/toggle/ — flip is_active."""
        product = self.get_object()
        product.is_active = not product.is_active
        product.save(update_fields=['is_active', 'updated_at'])
        return Response({'id': product.id, 'is_active': product.is_active})


class MediLinkIncomeViewSet(viewsets.ModelViewSet):
    """
    Income records for MediLink.  Represents money flowing TO MediLink
    (product sales, subscription fees, etc.).
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['product__name', 'buyer__email', 'reference', 'notes']
    ordering_fields = ['sale_date', 'total_amount', 'status']
    ordering = ['-sale_date']
    serializer_class = MediLinkSaleSerializer

    def get_queryset(self):
        qs = MediLinkSale.objects.select_related('product', 'buyer', 'recorded_by')

        sale_status = self.request.query_params.get('status')
        product_id = self.request.query_params.get('product_id')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if sale_status:
            qs = qs.filter(status=sale_status)
        if product_id:
            qs = qs.filter(product_id=product_id)
        if date_from:
            qs = qs.filter(sale_date__date__gte=date_from)
        if date_to:
            qs = qs.filter(sale_date__date__lte=date_to)

        return qs

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """GET /api/admin/income/stats/ — aggregate income statistics."""
        now = timezone.now()

        total_sales = MediLinkSale.objects.count()
        completed_sales = MediLinkSale.objects.filter(status=SaleStatus.COMPLETED).count()
        refunded_sales = MediLinkSale.objects.filter(status=SaleStatus.REFUNDED).count()
        pending_sales = MediLinkSale.objects.filter(status=SaleStatus.PENDING).count()

        total_revenue = (
            MediLinkSale.objects.filter(status=SaleStatus.COMPLETED)
            .aggregate(t=Sum('total_amount'))['t'] or Decimal('0')
        )
        this_month_revenue = (
            MediLinkSale.objects.filter(
                status=SaleStatus.COMPLETED,
                sale_date__year=now.year,
                sale_date__month=now.month,
            ).aggregate(t=Sum('total_amount'))['t'] or Decimal('0')
        )

        # Monthly trend (last 6 months)
        six_months_ago = now - timezone.timedelta(days=180)
        monthly = (
            MediLinkSale.objects
            .filter(status=SaleStatus.COMPLETED, sale_date__gte=six_months_ago)
            .annotate(month=TruncMonth('sale_date'))
            .values('month')
            .annotate(total=Sum('total_amount'), count=Count('id'))
            .order_by('month')
        )
        monthly_trend = [
            {
                'month': entry['month'].strftime('%Y-%m'),
                'total': str(entry['total'] or 0),
                'count': entry['count'],
            }
            for entry in monthly
        ]

        # Top products by revenue
        top_products = (
            MediLinkSale.objects
            .filter(status=SaleStatus.COMPLETED)
            .values('product__id', 'product__name')
            .annotate(revenue=Sum('total_amount'), units=Sum('quantity'))
            .order_by('-revenue')[:5]
        )

        return Response({
            'total_sales': total_sales,
            'completed_sales': completed_sales,
            'refunded_sales': refunded_sales,
            'pending_sales': pending_sales,
            'total_revenue': str(total_revenue),
            'this_month_revenue': str(this_month_revenue),
            'monthly_trend': monthly_trend,
            'top_products': [
                {
                    'product_id': p['product__id'],
                    'product_name': p['product__name'] or 'Manual Entry',
                    'revenue': str(p['revenue'] or 0),
                    'units': p['units'] or 0,
                }
                for p in top_products
            ],
        })
