"""
Admin views for MediLink income records under the legacy /invoices endpoints.

This keeps backward compatibility while ensuring admin "invoices" only show
MediLink income (platform sales/subscriptions), not provider-to-patient invoices.
"""
from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from admins.models.products import MediLinkSale, SaleStatus
from admins.permissions import IsAdmin


class AdminInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset returning MediLink income records via /api/admin/invoices/.
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        'product__name',
        'buyer__email',
        'reference',
        'notes',
    ]
    ordering_fields = ['sale_date', 'total_amount', 'status']
    ordering = ['-sale_date']

    def get_queryset(self):
        qs = MediLinkSale.objects.select_related('product', 'buyer', 'recorded_by').order_by('-sale_date')

        # Optional date range filtering
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        sale_status = self.request.query_params.get('status')
        product_id = self.request.query_params.get('product_id')

        if date_from:
            qs = qs.filter(sale_date__date__gte=date_from)
        if date_to:
            qs = qs.filter(sale_date__date__lte=date_to)
        if sale_status:
            qs = qs.filter(status=sale_status)
        if product_id:
            qs = qs.filter(product_id=product_id)

        return qs

    def get_serializer_class(self):
        from admins.serializers.products import MediLinkSaleSerializer
        return MediLinkSaleSerializer

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """GET /api/admin/invoices/stats/ - MediLink income-only aggregate stats."""

        now = timezone.now()

        total = MediLinkSale.objects.count()
        paid = MediLinkSale.objects.filter(status=SaleStatus.COMPLETED).count()
        overdue = 0
        draft = MediLinkSale.objects.filter(status=SaleStatus.PENDING).count()
        cancelled = MediLinkSale.objects.filter(status=SaleStatus.CANCELLED).count()
        pending = MediLinkSale.objects.filter(status=SaleStatus.PENDING).count()

        total_revenue = MediLinkSale.objects.filter(status=SaleStatus.COMPLETED).aggregate(t=Sum('total_amount'))['t'] or Decimal('0')
        outstanding = MediLinkSale.objects.filter(status=SaleStatus.PENDING).aggregate(t=Sum('total_amount'))['t'] or Decimal('0')

        this_month_revenue = MediLinkSale.objects.filter(
            status=SaleStatus.COMPLETED,
            sale_date__year=now.year,
            sale_date__month=now.month,
        ).aggregate(t=Sum('total_amount'))['t'] or Decimal('0')

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

        return Response({
            'total': total,
            'paid': paid,
            'overdue': overdue,
            'draft': draft,
            'cancelled': cancelled,
            'pending': pending,
            'total_revenue': str(total_revenue),
            'outstanding_balance': str(outstanding),
            'this_month_revenue': str(this_month_revenue),
            'monthly_trend': [
                {'month': str(e['month'].date())[:7], 'total': str(e['total']), 'count': e['count']}
                for e in monthly
            ],
        })

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """POST /api/admin/invoices/{id}/cancel/ - cancel a pending income record."""
        sale = self.get_object()
        if sale.status == SaleStatus.CANCELLED:
            return Response({'error': 'Income record is already cancelled.'}, status=400)
        if sale.status == SaleStatus.COMPLETED:
            return Response({'error': 'Completed income cannot be cancelled. Use REFUNDED instead.'}, status=400)
        sale.status = SaleStatus.CANCELLED
        sale.save(update_fields=['status', 'updated_at'])
        return Response({'message': 'Income record cancelled successfully.'})
