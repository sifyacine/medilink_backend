"""
Admin views for platform-wide invoice oversight.

Endpoints:
  GET /api/admin/invoices/              List all invoices (filterable)
  GET /api/admin/invoices/{id}/         Invoice detail
  GET /api/admin/invoices/stats/        Aggregate invoice statistics
  POST /api/admin/invoices/{id}/cancel/ Cancel an invoice (admin override)
"""
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from admins.permissions import IsAdmin


class AdminInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin read-only viewset for browsing all platform invoices.
    Provides an additional /stats/ list action and /cancel/ detail action.
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'invoice_type', 'currency']
    search_fields = [
        'invoice_number',
        'provider__user__email',
        'patient__email',
        'patient__first_name',
        'patient__last_name',
    ]
    ordering_fields = ['created_at', 'due_date', 'total', 'paid_at']
    ordering = ['-created_at']

    def get_queryset(self):
        from invoices.models import Invoice
        qs = Invoice.objects.select_related(
            'provider__user', 'patient',
        ).order_by('-created_at')

        # Optional date range filtering
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        provider_id = self.request.query_params.get('provider_id')

        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        if provider_id:
            qs = qs.filter(provider_id=provider_id)

        return qs

    def get_serializer_class(self):
        from admins.serializers.invoices import AdminInvoiceListSerializer, AdminInvoiceDetailSerializer
        if self.action == 'list':
            return AdminInvoiceListSerializer
        return AdminInvoiceDetailSerializer

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """GET /api/admin/invoices/stats/ -- aggregate invoice statistics."""
        from invoices.models import Invoice
        from decimal import Decimal

        now = timezone.now()

        total = Invoice.objects.count()
        paid = Invoice.objects.filter(status='PAID').count()
        overdue = Invoice.objects.filter(status='OVERDUE').count()
        draft = Invoice.objects.filter(status='DRAFT').count()
        cancelled = Invoice.objects.filter(status='CANCELLED').count()
        pending = Invoice.objects.filter(status__in=['SENT', 'VIEWED', 'PARTIALLY_PAID']).count()

        total_revenue = Invoice.objects.filter(status='PAID').aggregate(t=Sum('total'))['t'] or Decimal('0')
        outstanding = Invoice.objects.filter(
            status__in=['SENT', 'VIEWED', 'OVERDUE', 'PARTIALLY_PAID']
        ).aggregate(t=Sum('total'))['t'] or Decimal('0')

        this_month_revenue = Invoice.objects.filter(
            status='PAID',
            paid_at__year=now.year,
            paid_at__month=now.month,
        ).aggregate(t=Sum('total'))['t'] or Decimal('0')

        # Monthly trend (last 6 months)
        six_months_ago = now - timezone.timedelta(days=180)
        monthly = (
            Invoice.objects
            .filter(status='PAID', paid_at__gte=six_months_ago)
            .annotate(month=TruncMonth('paid_at'))
            .values('month')
            .annotate(total=Sum('total'), count=Count('id'))
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
        """POST /api/admin/invoices/{id}/cancel/ -- admin force-cancel an invoice."""
        from invoices.models import Invoice
        from admins.services import log_admin_action, get_client_ip
        from common.enums import AdminActionType

        try:
            invoice = self.get_object()
        except Exception:
            return Response({'error': 'Invoice not found.'}, status=status.HTTP_404_NOT_FOUND)

        if invoice.status == 'CANCELLED':
            return Response({'error': 'Invoice is already cancelled.'}, status=status.HTTP_400_BAD_REQUEST)
        if invoice.status == 'PAID':
            return Response({'error': 'Cannot cancel a paid invoice.'}, status=status.HTTP_400_BAD_REQUEST)

        invoice.status = 'CANCELLED'
        invoice.notes = (invoice.notes or '') + f'\n[Admin cancelled by {request.user.email}]'
        invoice.save(update_fields=['status', 'notes'])

        log_admin_action(
            admin=request.user,
            action=AdminActionType.CONTENT_UPDATE,
            target_obj=invoice,
            ip=get_client_ip(request),
            extra={'action': 'admin_cancel', 'invoice_number': invoice.invoice_number},
        )

        return Response({'message': 'Invoice cancelled successfully.'})
