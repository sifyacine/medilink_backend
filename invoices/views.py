"""
Invoice views for the Medilink platform.

Provides API endpoints for:
- Invoice CRUD operations
- Invoice item management
- Payment recording and verification
- Invoice actions (send, cancel, mark paid)
- Statistics and reports
"""
from decimal import Decimal
from datetime import timedelta

from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import (
    Invoice, InvoiceItem, Payment, InvoiceActivity,
    InvoiceStatus, InvoiceType, ItemType
)
from .serializers import (
    InvoiceSerializer, InvoiceListSerializer, InvoiceCreateSerializer,
    InvoiceItemSerializer, InvoiceItemCreateSerializer,
    PaymentSerializer, PaymentVerifySerializer,
    InvoiceActivitySerializer,
    InvoiceSendSerializer, InvoiceCancelSerializer,
    InvoiceFromAppointmentSerializer, InvoiceStatisticsSerializer,
)
from .permissions import (
    IsProviderOwner, IsInvoiceParticipant, CanManageInvoice,
    CanViewInvoice, CanManagePayment,
)
from common.enums import UserRole


class InvoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing invoices.
    
    Endpoints:
    - GET /invoices/ - List invoices
    - POST /invoices/ - Create invoice
    - GET /invoices/{id}/ - Get invoice details
    - PUT/PATCH /invoices/{id}/ - Update invoice
    - DELETE /invoices/{id}/ - Delete invoice (draft only)
    
    Actions:
    - POST /invoices/{id}/send/ - Send invoice to patient
    - POST /invoices/{id}/cancel/ - Cancel invoice
    - POST /invoices/{id}/mark_viewed/ - Mark as viewed
    - POST /invoices/{id}/add_item/ - Add item to invoice
    - POST /invoices/{id}/remove_item/ - Remove item from invoice
    - POST /invoices/{id}/record_payment/ - Record a payment
    - GET /invoices/{id}/activities/ - Get activity log
    - POST /invoices/from_appointment/ - Create from appointment
    - GET /invoices/statistics/ - Get invoice statistics
    - GET /invoices/overdue/ - Get overdue invoices
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter invoices based on user role."""
        user = self.request.user
        queryset = Invoice.objects.select_related(
            'provider', 'provider__user',
            'patient_user', 'patient_record',
            'appointment', 'prescription',
        ).prefetch_related('items', 'payments')
        
        if user.role == UserRole.ADMIN:
            return queryset
        
        if user.role == UserRole.PROVIDER:
            if hasattr(user, 'provider_profile'):
                return queryset.filter(provider=user.provider_profile)
            return queryset.none()
        
        if user.role == UserRole.PATIENT:
            return queryset.filter(
                Q(patient_user=user) |
                Q(patient_record__linked_user=user)
            )
        
        return queryset.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return InvoiceListSerializer
        if self.action == 'create':
            return InvoiceCreateSerializer
        return InvoiceSerializer
    
    def get_permissions(self):
        """Return appropriate permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageInvoice()]
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        if self.action in ['send', 'cancel', 'add_item', 'remove_item', 'record_payment']:
            return [IsAuthenticated(), CanManageInvoice()]
        if self.action == 'mark_viewed':
            return [IsAuthenticated()]
        return [IsAuthenticated()]
    
    def destroy(self, request, *args, **kwargs):
        """Only allow deleting draft invoices."""
        invoice = self.get_object()
        if invoice.status != InvoiceStatus.DRAFT:
            return Response(
                {'error': 'Can only delete draft invoices. Cancel the invoice instead.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """
        Send invoice to patient.
        Changes status from DRAFT to SENT.
        """
        invoice = self.get_object()
        serializer = InvoiceSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if invoice.status != InvoiceStatus.DRAFT:
            return Response(
                {'error': 'Invoice has already been sent.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not invoice.items.exists():
            return Response(
                {'error': 'Cannot send invoice without items.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status
        invoice.mark_as_sent()
        
        # Log activity
        InvoiceActivity.objects.create(
            invoice=invoice,
            activity_type='SENT',
            description=f'Invoice sent to {invoice.get_patient_display_name()}',
            performed_by=request.user,
        )
        
        # Send notification if requested
        if serializer.validated_data.get('send_notification', True):
            # TODO: Integrate with notification system
            pass
        
        return Response(
            InvoiceSerializer(invoice, context={'request': request}).data
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an invoice."""
        invoice = self.get_object()
        serializer = InvoiceCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if invoice.status in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]:
            return Response(
                {'error': f'Cannot cancel invoice with status {invoice.status}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Record old status
        old_status = invoice.status
        
        # Update invoice
        invoice.status = InvoiceStatus.CANCELLED
        invoice.cancelled_at = timezone.now()
        invoice.cancelled_by = request.user
        invoice.cancellation_reason = serializer.validated_data['reason']
        invoice.save()
        
        # Log activity
        InvoiceActivity.objects.create(
            invoice=invoice,
            activity_type='CANCELLED',
            description=f'Invoice cancelled: {serializer.validated_data["reason"]}',
            old_value={'status': old_status},
            new_value={'status': InvoiceStatus.CANCELLED},
            performed_by=request.user,
        )
        
        return Response(
            InvoiceSerializer(invoice, context={'request': request}).data
        )
    
    @action(detail=True, methods=['post'])
    def mark_viewed(self, request, pk=None):
        """Mark invoice as viewed by patient."""
        invoice = self.get_object()
        
        # Only the patient can mark as viewed
        is_patient = (
            invoice.patient_user == request.user or
            (invoice.patient_record and invoice.patient_record.linked_user == request.user)
        )
        
        if not is_patient and request.user.role != UserRole.ADMIN:
            return Response(
                {'error': 'Only the patient can mark invoice as viewed.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if invoice.status == InvoiceStatus.SENT:
            invoice.mark_as_viewed()
            
            InvoiceActivity.objects.create(
                invoice=invoice,
                activity_type='VIEWED',
                description='Invoice viewed by patient',
                performed_by=request.user,
            )
        
        return Response(
            InvoiceSerializer(invoice, context={'request': request}).data
        )
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add an item to the invoice."""
        invoice = self.get_object()
        
        if invoice.status != InvoiceStatus.DRAFT:
            return Response(
                {'error': 'Can only add items to draft invoices.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = InvoiceItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            # Create the item
            item_data = serializer.validated_data.copy()
            service = item_data.pop('service', None)
            custom_service = item_data.pop('custom_service', None)
            item_data.pop('service_id', None)
            item_data.pop('custom_service_id', None)
            
            item = InvoiceItem.objects.create(
                invoice=invoice,
                service=service,
                custom_service=custom_service,
                **item_data
            )
            
            # Recalculate totals
            invoice.calculate_totals()
            invoice.save()
            
            # Log activity
            InvoiceActivity.objects.create(
                invoice=invoice,
                activity_type='ITEM_ADDED',
                description=f'Item added: {item.description}',
                new_value={
                    'description': item.description,
                    'quantity': str(item.quantity),
                    'unit_price': str(item.unit_price),
                    'total': str(item.total),
                },
                performed_by=request.user,
            )
        
        return Response(
            InvoiceSerializer(invoice, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def remove_item(self, request, pk=None):
        """Remove an item from the invoice."""
        invoice = self.get_object()
        
        if invoice.status != InvoiceStatus.DRAFT:
            return Response(
                {'error': 'Can only remove items from draft invoices.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        item_id = request.data.get('item_id')
        if not item_id:
            return Response(
                {'error': 'item_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            item = invoice.items.get(id=item_id)
        except InvoiceItem.DoesNotExist:
            return Response(
                {'error': 'Item not found on this invoice.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        with transaction.atomic():
            item_description = item.description
            item.delete()
            
            # Recalculate totals
            invoice.calculate_totals()
            invoice.save()
            
            # Log activity
            InvoiceActivity.objects.create(
                invoice=invoice,
                activity_type='ITEM_REMOVED',
                description=f'Item removed: {item_description}',
                performed_by=request.user,
            )
        
        return Response(
            InvoiceSerializer(invoice, context={'request': request}).data
        )
    
    @action(detail=True, methods=['post'])
    def record_payment(self, request, pk=None):
        """Record a payment for the invoice."""
        invoice = self.get_object()
        
        if invoice.status in [InvoiceStatus.DRAFT, InvoiceStatus.CANCELLED]:
            return Response(
                {'error': f'Cannot record payment for invoice with status {invoice.status}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        request.data['invoice'] = invoice.id
        serializer = PaymentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            payment = serializer.save()
            
            # Log activity
            InvoiceActivity.objects.create(
                invoice=invoice,
                activity_type='PAYMENT_RECEIVED',
                description=f'Payment of {payment.amount} {invoice.currency} received via {payment.get_payment_method_display()}',
                new_value={
                    'amount': str(payment.amount),
                    'method': payment.payment_method,
                    'reference': payment.reference_number,
                },
                performed_by=request.user,
            )
        
        return Response(
            InvoiceSerializer(invoice, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        """Get activity log for an invoice."""
        invoice = self.get_object()
        activities = invoice.activities.all()
        serializer = InvoiceActivitySerializer(activities, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def from_appointment(self, request):
        """
        Create an invoice from a completed appointment.
        """
        serializer = InvoiceFromAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        from appointments.models import Appointment
        
        appointment = Appointment.objects.get(
            id=serializer.validated_data['appointment_id']
        )
        
        # Check permission - user must be the provider
        if request.user.role != UserRole.ADMIN:
            if not hasattr(request.user, 'provider_profile'):
                return Response(
                    {'error': 'Only providers can create invoices.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            if appointment.provider != request.user.provider_profile:
                return Response(
                    {'error': 'You can only create invoices for your own appointments.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Check if invoice already exists for this appointment
        if Invoice.objects.filter(appointment=appointment).exists():
            return Response(
                {'error': 'An invoice already exists for this appointment.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Create invoice
            due_date = timezone.now().date() + timedelta(
                days=serializer.validated_data.get('due_days', 30)
            )
            
            invoice = Invoice.objects.create(
                provider=appointment.provider,
                patient_user=appointment.patient_user,
                patient_record=appointment.patient_record,
                invoice_type=InvoiceType.SERVICE,
                appointment=appointment,
                issue_date=timezone.now().date(),
                due_date=due_date,
                tax_rate=serializer.validated_data.get('tax_rate', Decimal('0.00')),
                notes=serializer.validated_data.get('notes', ''),
                created_by=request.user,
            )
            
            # Add services from appointment
            if serializer.validated_data.get('include_services', True):
                # Add primary service
                if appointment.service:
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        item_type=ItemType.SERVICE,
                        service=appointment.service,
                        description=appointment.service.title,
                        description_en=appointment.service.title_en or appointment.service.title,
                        quantity=Decimal('1.00'),
                        unit='session',
                        unit_price=appointment.service.price,
                    )
                
                # Add additional services
                for apt_service in appointment.appointment_services.select_related('service').all():
                    if apt_service.service != appointment.service:
                        InvoiceItem.objects.create(
                            invoice=invoice,
                            item_type=ItemType.SERVICE,
                            service=apt_service.service,
                            description=apt_service.service.title,
                            description_en=apt_service.service.title_en or apt_service.service.title,
                            quantity=Decimal('1.00'),
                            unit='session',
                            unit_price=apt_service.service.price,
                        )
            
            # Calculate totals
            invoice.calculate_totals()
            invoice.save()
            
            # Log activity
            InvoiceActivity.objects.create(
                invoice=invoice,
                activity_type='CREATED',
                description=f'Invoice created from appointment on {appointment.scheduled_date}',
                performed_by=request.user,
            )
        
        return Response(
            InvoiceSerializer(invoice, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get invoice statistics for the current provider.
        """
        queryset = self.get_queryset()
        
        # Filter by date range if provided
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(issue_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(issue_date__lte=end_date)
        
        # Aggregate statistics
        stats = queryset.aggregate(
            total_amount=Sum('total'),
            total_paid=Sum('amount_paid'),
        )
        
        # Count by status
        status_counts = queryset.values('status').annotate(count=Count('id'))
        status_dict = {item['status']: item['count'] for item in status_counts}
        
        # Count by type
        type_counts = queryset.values('invoice_type').annotate(count=Count('id'))
        type_dict = {item['invoice_type']: item['count'] for item in type_counts}
        
        data = {
            'total_invoices': queryset.count(),
            'total_amount': stats['total_amount'] or Decimal('0.00'),
            'total_paid': stats['total_paid'] or Decimal('0.00'),
            'total_outstanding': (stats['total_amount'] or Decimal('0.00')) - (stats['total_paid'] or Decimal('0.00')),
            'draft_count': status_dict.get(InvoiceStatus.DRAFT, 0),
            'sent_count': status_dict.get(InvoiceStatus.SENT, 0) + status_dict.get(InvoiceStatus.VIEWED, 0),
            'paid_count': status_dict.get(InvoiceStatus.PAID, 0),
            'overdue_count': status_dict.get(InvoiceStatus.OVERDUE, 0),
            'cancelled_count': status_dict.get(InvoiceStatus.CANCELLED, 0),
            'service_invoices': type_dict.get(InvoiceType.SERVICE, 0),
            'product_invoices': type_dict.get(InvoiceType.PRODUCT, 0),
            'mixed_invoices': type_dict.get(InvoiceType.MIXED, 0),
            'custom_invoices': type_dict.get(InvoiceType.CUSTOM, 0),
        }
        
        serializer = InvoiceStatisticsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """
        Get list of overdue invoices.
        Also updates any newly overdue invoices.
        """
        queryset = self.get_queryset()
        today = timezone.now().date()
        
        # Find and update newly overdue invoices
        newly_overdue = queryset.filter(
            status__in=[InvoiceStatus.SENT, InvoiceStatus.VIEWED, InvoiceStatus.PARTIALLY_PAID],
            due_date__lt=today,
        )
        
        for invoice in newly_overdue:
            invoice.status = InvoiceStatus.OVERDUE
            invoice.save(update_fields=['status', 'updated_at'])
        
        # Return all overdue invoices
        overdue_invoices = queryset.filter(status=InvoiceStatus.OVERDUE)
        serializer = InvoiceListSerializer(overdue_invoices, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def uninvoiced_appointments(self, request):
        """
        Get list of completed appointments without invoices.
        
        Helps doctors identify appointments that need to be invoiced.
        
        Query Parameters:
        - start_date: Filter from date (YYYY-MM-DD)
        - end_date: Filter to date (YYYY-MM-DD)
        """
        from appointments.models import Appointment, AppointmentStatus
        from appointments.serializers import AppointmentListSerializer as AppointmentSerializer
        
        user = request.user
        
        # Get provider
        if user.role != UserRole.PROVIDER:
            if user.role != UserRole.ADMIN:
                return Response(
                    {'error': 'Only providers can access uninvoiced appointments.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Get completed appointments without invoices
        queryset = Appointment.objects.filter(
            status=AppointmentStatus.COMPLETED
        ).exclude(
            invoices__isnull=False  # Exclude appointments that have invoices
        )
        
        # Filter by provider if not admin
        if user.role == UserRole.PROVIDER:
            if hasattr(user, 'provider_profile'):
                queryset = queryset.filter(provider=user.provider_profile)
            else:
                return Response([])
        
        # Date filters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(scheduled_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(scheduled_date__lte=end_date)
        
        queryset = queryset.order_by('-scheduled_date')[:50]  # Limit to 50
        
        serializer = AppointmentSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def financial_summary(self, request):
        """
        Get comprehensive financial summary for providers.
        
        Includes:
        - Total revenue (paid invoices)
        - Outstanding amount (unpaid)
        - Revenue by service type
        - Monthly breakdown
        - Payment method distribution
        
        Query Parameters:
        - period: 'week', 'month', 'quarter', 'year' (default: 'month')
        - start_date: Custom start date (YYYY-MM-DD)
        - end_date: Custom end date (YYYY-MM-DD)
        """
        queryset = self.get_queryset()
        
        # Determine date range
        period = request.query_params.get('period', 'month')
        today = timezone.now().date()
        
        if request.query_params.get('start_date'):
            start_date = request.query_params.get('start_date')
        else:
            if period == 'week':
                start_date = today - timedelta(days=7)
            elif period == 'month':
                start_date = today - timedelta(days=30)
            elif period == 'quarter':
                start_date = today - timedelta(days=90)
            elif period == 'year':
                start_date = today - timedelta(days=365)
            else:
                start_date = today - timedelta(days=30)
        
        end_date = request.query_params.get('end_date', today)
        
        # Filter by date range
        queryset = queryset.filter(issue_date__gte=start_date, issue_date__lte=end_date)
        
        # Calculate totals
        from django.db.models.functions import TruncMonth
        
        total_revenue = queryset.filter(
            status=InvoiceStatus.PAID
        ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')
        
        total_outstanding = queryset.filter(
            status__in=[InvoiceStatus.SENT, InvoiceStatus.VIEWED, 
                       InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE]
        ).aggregate(
            total=Sum('total'),
            paid=Sum('amount_paid')
        )
        outstanding = (total_outstanding['total'] or Decimal('0.00')) - (total_outstanding['paid'] or Decimal('0.00'))
        
        # Revenue by invoice type
        revenue_by_type = queryset.filter(
            status=InvoiceStatus.PAID
        ).values('invoice_type').annotate(
            total=Sum('total'),
            count=Count('id')
        )
        
        # Payment method distribution (from payments on paid invoices)
        payment_methods = Payment.objects.filter(
            invoice__in=queryset.filter(status=InvoiceStatus.PAID),
            is_refund=False
        ).values('payment_method').annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        # Monthly revenue trend
        monthly_revenue = queryset.filter(
            status=InvoiceStatus.PAID
        ).annotate(
            month=TruncMonth('paid_at')
        ).values('month').annotate(
            total=Sum('total'),
            count=Count('id')
        ).order_by('month')
        
        # Uninvoiced appointments count
        from appointments.models import Appointment, AppointmentStatus
        uninvoiced_count = 0
        if hasattr(request.user, 'provider_profile'):
            uninvoiced_count = Appointment.objects.filter(
                provider=request.user.provider_profile,
                status=AppointmentStatus.COMPLETED
            ).exclude(
                invoices__isnull=False
            ).count()
        
        data = {
            'period': period,
            'start_date': str(start_date),
            'end_date': str(end_date),
            'total_revenue': total_revenue,
            'total_outstanding': outstanding,
            'uninvoiced_appointments': uninvoiced_count,
            'revenue_by_type': list(revenue_by_type),
            'payment_methods': list(payment_methods),
            'monthly_revenue': list(monthly_revenue),
            'invoices_count': queryset.count(),
            'paid_count': queryset.filter(status=InvoiceStatus.PAID).count(),
            'pending_count': queryset.filter(
                status__in=[InvoiceStatus.SENT, InvoiceStatus.VIEWED, InvoiceStatus.PARTIALLY_PAID]
            ).count(),
            'overdue_count': queryset.filter(status=InvoiceStatus.OVERDUE).count(),
        }
        
        return Response(data)


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payments.
    
    Mostly accessed through invoice endpoints, but provides
    direct access for payment management.
    """
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, CanManagePayment]
    
    def get_queryset(self):
        """Filter payments based on user role."""
        user = self.request.user
        queryset = Payment.objects.select_related(
            'invoice', 'invoice__provider', 'invoice__provider__user',
        )
        
        if user.role == UserRole.ADMIN:
            return queryset
        
        if user.role == UserRole.PROVIDER:
            if hasattr(user, 'provider_profile'):
                return queryset.filter(invoice__provider=user.provider_profile)
            return queryset.none()
        
        if user.role == UserRole.PATIENT:
            return queryset.filter(
                Q(invoice__patient_user=user) |
                Q(invoice__patient_record__linked_user=user)
            )
        
        return queryset.none()
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a payment."""
        payment = self.get_object()
        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        payment.is_verified = serializer.validated_data['is_verified']
        payment.verified_at = timezone.now()
        payment.verified_by = request.user
        
        if serializer.validated_data.get('notes'):
            payment.notes = serializer.validated_data['notes']
        
        payment.save()
        
        return Response(PaymentSerializer(payment).data)
    
    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """Create a refund for a payment."""
        original_payment = self.get_object()
        
        refund_amount = Decimal(request.data.get('amount', str(original_payment.amount)))
        refund_reason = request.data.get('reason', '')
        
        if not refund_reason:
            return Response(
                {'error': 'Refund reason is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if refund_amount > original_payment.amount:
            return Response(
                {'error': 'Refund amount cannot exceed original payment.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already refunded
        existing_refunds = original_payment.refunds.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        if existing_refunds + refund_amount > original_payment.amount:
            return Response(
                {'error': f'Total refunds would exceed original payment. Already refunded: {existing_refunds}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            refund = Payment.objects.create(
                invoice=original_payment.invoice,
                amount=refund_amount,
                payment_method=original_payment.payment_method,
                is_refund=True,
                refund_reason=refund_reason,
                original_payment=original_payment,
                recorded_by=request.user,
            )
            
            # Log activity
            InvoiceActivity.objects.create(
                invoice=original_payment.invoice,
                activity_type='PAYMENT_REFUNDED',
                description=f'Refund of {refund_amount} issued',
                new_value={
                    'amount': str(refund_amount),
                    'reason': refund_reason,
                    'original_payment': str(original_payment.id),
                },
                performed_by=request.user,
            )
            
            # Update invoice status if fully refunded
            invoice = original_payment.invoice
            if invoice.amount_paid <= Decimal('0.00'):
                if invoice.status == InvoiceStatus.PAID:
                    invoice.status = InvoiceStatus.REFUNDED
                    invoice.save()
        
        return Response(PaymentSerializer(refund).data, status=status.HTTP_201_CREATED)


class PatientInvoiceListView(generics.ListAPIView):
    """
    List invoices for the current patient.
    Simplified view for patient-facing applications.
    """
    serializer_class = InvoiceListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Invoice.objects.filter(
            Q(patient_user=user) |
            Q(patient_record__linked_user=user)
        ).exclude(
            status=InvoiceStatus.DRAFT  # Don't show drafts to patients
        ).select_related(
            'provider', 'provider__user'
        ).order_by('-created_at')
