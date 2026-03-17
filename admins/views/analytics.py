"""
Admin analytics views -- platform-wide statistics using ORM aggregations.

Endpoints:
  GET /api/admin/analytics/overview/
  GET /api/admin/analytics/users/?period=daily|weekly|monthly
  GET /api/admin/analytics/appointments/
  GET /api/admin/analytics/revenue/
  GET /api/admin/analytics/providers/
"""
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from admins.permissions import IsAdmin
from common.enums import ProviderStatus, ProviderType, UserAccountStatus


class OverviewView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        from providers.models import Provider
        from patients.models import PatientRecord

        now = timezone.now()

        total_users = User.objects.count()
        active_users = User.objects.filter(account_status=UserAccountStatus.ACTIVE).count()
        suspended_users = User.objects.filter(account_status=UserAccountStatus.SUSPENDED).count()
        new_users_this_month = User.objects.filter(
            created_at__year=now.year, created_at__month=now.month
        ).count()

        total_providers = Provider.objects.count()
        pending_providers = Provider.objects.filter(status=ProviderStatus.PENDING).count()
        new_providers_this_month = Provider.objects.filter(
            created_at__year=now.year, created_at__month=now.month
        ).count()

        total_patients = PatientRecord.objects.filter(is_deleted=False).count()

        total_appointments = 0
        try:
            from appointments.models import Appointment
            total_appointments = Appointment.objects.count()
        except Exception:
            pass

        total_revenue = Decimal('0.00')
        total_invoices = 0
        paid_invoices = 0
        pending_invoices = 0
        try:
            from invoices.models import Invoice
            total_invoices = Invoice.objects.count()
            paid_invoices = Invoice.objects.filter(status='PAID').count()
            pending_invoices = Invoice.objects.filter(status__in=['SENT', 'VIEWED', 'OVERDUE', 'PARTIALLY_PAID']).count()
            result = Invoice.objects.filter(status='PAID').aggregate(total=Sum('total'))
            total_revenue = result['total'] or Decimal('0.00')
        except Exception:
            pass

        return Response({
            'total_users': total_users,
            'total_providers': total_providers,
            'total_patients': total_patients,
            'total_appointments': total_appointments,
            'pending_providers': pending_providers,
            'active_users': active_users,
            'suspended_users': suspended_users,
            'total_revenue': str(total_revenue),
            'new_users_this_month': new_users_this_month,
            'new_providers_this_month': new_providers_this_month,
            'total_invoices': total_invoices,
            'paid_invoices': paid_invoices,
            'pending_invoices': pending_invoices,
        })


class UserStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        period = request.query_params.get('period', 'daily')
        role_filter = request.query_params.get('role')

        qs = User.objects.all()
        if role_filter:
            qs = qs.filter(role=role_filter)

        if period == 'monthly':
            trunc_fn = TruncMonth
        elif period == 'weekly':
            trunc_fn = TruncWeek
        else:
            trunc_fn = TruncDay

        data = (
            qs
            .annotate(date=trunc_fn('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        return Response([
            {'date': entry['date'].date(), 'count': entry['count']}
            for entry in data
        ])


class AppointmentStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        try:
            from appointments.models import Appointment
            import datetime

            status_dist = (
                Appointment.objects.values('status')
                .annotate(count=Count('id'))
                .order_by('status')
            )

            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            daily = (
                Appointment.objects
                .filter(created_at__gte=thirty_days_ago)
                .annotate(date=TruncDay('created_at'))
                .values('date')
                .annotate(count=Count('id'))
                .order_by('date')
            )

            return Response({
                'status_distribution': list(status_dist),
                'daily_trend': [
                    {'date': e['date'].date(), 'count': e['count']}
                    for e in daily
                ],
            })
        except Exception as exc:
            return Response({'error': str(exc), 'status_distribution': [], 'daily_trend': []})


class RevenueStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        try:
            from invoices.models import Invoice, Payment

            twelve_months_ago = timezone.now() - timezone.timedelta(days=365)
            monthly = (
                Invoice.objects
                .filter(status='PAID', paid_at__gte=twelve_months_ago)
                .annotate(month=TruncMonth('paid_at'))
                .values('month')
                .annotate(total=Sum('total'), count=Count('id'))
                .order_by('month')
            )

            pm_breakdown = (
                Payment.objects
                .filter(is_refund=False)
                .values('payment_method')
                .annotate(total=Sum('amount'), count=Count('id'))
                .order_by('-total')
            )

            outstanding = Invoice.objects.filter(
                status__in=['SENT', 'VIEWED', 'OVERDUE', 'PARTIALLY_PAID']
            ).aggregate(total=Sum('total'))

            return Response({
                'monthly_revenue': [
                    {
                        'month': e['month'].date(),
                        'total': str(e['total'] or Decimal('0.00')),
                        'count': e['count'],
                    }
                    for e in monthly
                ],
                'payment_method_breakdown': list(pm_breakdown),
                'outstanding_balance': str(outstanding['total'] or Decimal('0.00')),
            })
        except Exception as exc:
            return Response({
                'error': str(exc),
                'monthly_revenue': [],
                'payment_method_breakdown': [],
                'outstanding_balance': '0.00',
            })


class ProviderStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        from providers.models import Provider

        status_dist = (
            Provider.objects.values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )

        type_stats = []
        for pt in ProviderType.values:
            qs = Provider.objects.filter(provider_type=pt)
            total = qs.count()
            if total == 0:
                continue
            type_stats.append({
                'provider_type': pt,
                'provider_type_display': ProviderType(pt).label,
                'total': total,
                'approved': qs.filter(status=ProviderStatus.APPROVED).count(),
                'pending': qs.filter(status=ProviderStatus.PENDING).count(),
                'refused': qs.filter(status=ProviderStatus.REFUSED).count(),
                'suspended': qs.filter(status=ProviderStatus.SUSPENDED).count(),
            })

        approved = Provider.objects.filter(status=ProviderStatus.APPROVED).count()
        refused = Provider.objects.filter(status=ProviderStatus.REFUSED).count()
        total_decided = approved + refused
        approval_rate = round((approved / total_decided * 100), 1) if total_decided > 0 else 0.0

        return Response({
            'status_distribution': list(status_dist),
            'type_distribution': type_stats,
            'approval_rate': approval_rate,
        })
