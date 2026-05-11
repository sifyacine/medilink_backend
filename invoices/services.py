"""
Invoice services and utilities for the Medilink platform.

Provides business logic for:
- Invoice creation from various sources
- Invoice notifications
- PDF generation preparation
- Invoice status management
- Recurring invoice support
"""
from decimal import Decimal
from datetime import timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from django.db import transaction
from django.utils import timezone

from .models import (
    Invoice, InvoiceItem, Payment, InvoiceActivity,
    InvoiceStatus, InvoiceType, PaymentMethod, ItemType,
)
from accounts.models import User
from providers.models.provider import Provider
from common.enums import ProviderType


@dataclass
class InvoiceItemData:
    """Data class for invoice item creation."""
    description: str
    unit_price: Decimal
    quantity: Decimal = Decimal('1.00')
    unit: str = 'unit'
    discount_percentage: Decimal = Decimal('0.00')
    item_type: str = ItemType.CUSTOM
    service_id: Optional[str] = None
    custom_service_id: Optional[str] = None
    description_en: str = ''
    description_ar: str = ''
    description_fr: str = ''
    notes: str = ''
    order: int = 0


@dataclass
class InvoiceConfig:
    """Configuration for invoice creation."""
    tax_rate: Decimal = Decimal('0.00')
    due_days: int = 30
    currency: str = 'DZD'
    discount_type: str = 'FIXED'
    discount_value: Decimal = Decimal('0.00')
    discount_reason: str = ''
    notes: str = ''
    terms: str = ''
    auto_send: bool = False


class InvoiceService:
    """
    Service class for invoice operations.
    
    Centralizes business logic for invoice creation and management.
    """
    
    @staticmethod
    @transaction.atomic
    def create_invoice(
        provider: Provider,
        patient_user: Optional[User] = None,
        patient_record=None,
        items: Optional[List[InvoiceItemData]] = None,
        config: Optional[InvoiceConfig] = None,
        appointment=None,
        prescription=None,
        nurse_request=None,
        created_by: Optional[User] = None,
    ) -> Invoice:
        """
        Create an invoice with the specified configuration.
        
        Args:
            provider: Provider issuing the invoice
            patient_user: Patient user account (optional)
            patient_record: Patient record (optional, if no user account)
            items: List of InvoiceItemData for line items
            config: InvoiceConfig for invoice settings
            appointment: Related appointment (optional)
            prescription: Related prescription (optional)
            nurse_request: Related nurse request (optional)
            created_by: User creating the invoice
        
        Returns:
            Created Invoice instance
        
        Raises:
            ValueError: If neither patient_user nor patient_record provided
        """
        if not patient_user and not patient_record:
            raise ValueError("Either patient_user or patient_record must be provided")
        
        config = config or InvoiceConfig()
        items = items or []
        
        # Determine invoice type based on items
        invoice_type = InvoiceService._determine_invoice_type(items)
        
        # Calculate due date
        due_date = timezone.now().date() + timedelta(days=config.due_days)
        
        # Create invoice
        invoice = Invoice.objects.create(
            provider=provider,
            patient_user=patient_user,
            patient_record=patient_record,
            invoice_type=invoice_type,
            appointment=appointment,
            prescription=prescription,
            nurse_request=nurse_request,
            issue_date=timezone.now().date(),
            due_date=due_date,
            currency=config.currency,
            tax_rate=config.tax_rate,
            discount_type=config.discount_type,
            discount_value=config.discount_value,
            discount_reason=config.discount_reason,
            notes=config.notes,
            terms=config.terms,
            created_by=created_by or provider.user,
        )
        
        # Create items
        for i, item_data in enumerate(items):
            InvoiceItem.objects.create(
                invoice=invoice,
                item_type=item_data.item_type,
                description=item_data.description,
                description_en=item_data.description_en or item_data.description,
                description_ar=item_data.description_ar,
                description_fr=item_data.description_fr,
                quantity=item_data.quantity,
                unit=item_data.unit,
                unit_price=item_data.unit_price,
                discount_percentage=item_data.discount_percentage,
                notes=item_data.notes,
                order=item_data.order or i,
            )
        
        # Calculate totals
        invoice.calculate_totals()
        invoice.save()
        
        # Log creation
        InvoiceActivity.objects.create(
            invoice=invoice,
            activity_type='CREATED',
            description=f'Invoice {invoice.invoice_number} created',
            performed_by=created_by,
        )
        
        # Auto-send if configured
        if config.auto_send and items:
            InvoiceService.send_invoice(invoice, created_by)
        
        return invoice
    
    @staticmethod
    def _determine_invoice_type(items: List[InvoiceItemData]) -> str:
        """Determine invoice type based on items."""
        if not items:
            return InvoiceType.CUSTOM
        
        has_services = any(
            item.item_type in [ItemType.SERVICE, ItemType.CUSTOM_SERVICE]
            for item in items
        )
        has_products = any(
            item.item_type in [ItemType.PRODUCT, ItemType.MEDICATION]
            for item in items
        )
        
        if has_services and has_products:
            return InvoiceType.MIXED
        elif has_products:
            return InvoiceType.PRODUCT
        elif has_services:
            return InvoiceType.SERVICE
        else:
            return InvoiceType.CUSTOM
    
    @staticmethod
    @transaction.atomic
    def create_from_appointment(
        appointment,
        config: Optional[InvoiceConfig] = None,
        created_by: Optional[User] = None,
        include_services: bool = True,
    ) -> Invoice:
        """
        Create an invoice from a completed appointment.
        
        Args:
            appointment: Completed Appointment instance
            config: Optional InvoiceConfig
            created_by: User creating the invoice
            include_services: Whether to include appointment services
        
        Returns:
            Created Invoice instance
        
        Raises:
            ValueError: If appointment is not completed or invoice exists
        """
        from appointments.models import AppointmentStatus
        
        if appointment.status != AppointmentStatus.COMPLETED:
            raise ValueError("Can only create invoice for completed appointments")
        
        if Invoice.objects.filter(appointment=appointment).exists():
            raise ValueError("Invoice already exists for this appointment")
        
        config = config or InvoiceConfig()
        items: List[InvoiceItemData] = []
        
        if include_services:
            # Add primary service
            if appointment.service:
                items.append(InvoiceItemData(
                    description=appointment.service.title,
                    description_en=appointment.service.title_en or appointment.service.title,
                    description_ar=appointment.service.title_ar or '',
                    description_fr=appointment.service.title_fr or '',
                    unit_price=appointment.service.price,
                    item_type=ItemType.SERVICE,
                    unit='session',
                ))
            
            # Add additional services
            for apt_service in appointment.appointment_services.select_related('service'):
                if apt_service.service != appointment.service:
                    items.append(InvoiceItemData(
                        description=apt_service.service.title,
                        description_en=apt_service.service.title_en or apt_service.service.title,
                        description_ar=apt_service.service.title_ar or '',
                        description_fr=apt_service.service.title_fr or '',
                        unit_price=apt_service.service.price,
                        item_type=ItemType.SERVICE,
                        unit='session',
                    ))
        
        return InvoiceService.create_invoice(
            provider=appointment.provider,
            patient_user=appointment.patient_user,
            patient_record=appointment.patient_record,
            items=items,
            config=config,
            appointment=appointment,
            created_by=created_by or appointment.provider.user,
        )
    
    @staticmethod
    @transaction.atomic
    def create_from_nurse_request(
        nurse_request,
        config: Optional[InvoiceConfig] = None,
        created_by: Optional[User] = None,
    ) -> Invoice:
        """
        Create an invoice from a completed nurse request.
        
        Args:
            nurse_request: Completed NurseRequest instance
            config: Optional InvoiceConfig
            created_by: User creating the invoice
        
        Returns:
            Created Invoice instance
        """
        from nurse_requests.models import RequestStatus
        
        if nurse_request.status != RequestStatus.COMPLETED:
            raise ValueError("Can only create invoice for completed nurse requests")
        
        if Invoice.objects.filter(nurse_request=nurse_request).exists():
            raise ValueError("Invoice already exists for this nurse request")
        
        config = config or InvoiceConfig()
        items: List[InvoiceItemData] = []
        
        # Add the service from the request
        if hasattr(nurse_request, 'service') and nurse_request.service:
            items.append(InvoiceItemData(
                description=nurse_request.service.title,
                unit_price=nurse_request.final_price or nurse_request.service.price,
                item_type=ItemType.SERVICE,
                unit='session',
            ))
        
        return InvoiceService.create_invoice(
            provider=nurse_request.nurse.provider,
            patient_user=nurse_request.patient_user,
            patient_record=nurse_request.patient_record,
            items=items,
            config=config,
            nurse_request=nurse_request,
            created_by=created_by,
        )
    
    @staticmethod
    def send_invoice(invoice: Invoice, sent_by: Optional[User] = None) -> bool:
        """
        Send an invoice to the patient.
        
        Updates status and sends notification.
        
        Args:
            invoice: Invoice to send
            sent_by: User sending the invoice
        
        Returns:
            True if successful
        """
        if invoice.status != InvoiceStatus.DRAFT:
            return False
        
        if not invoice.items.exists():
            return False
        
        invoice.mark_as_sent()
        
        InvoiceActivity.objects.create(
            invoice=invoice,
            activity_type='SENT',
            description=f'Invoice sent to {invoice.get_patient_display_name()}',
            performed_by=sent_by,
        )
        
        # Send notification
        InvoiceNotifier.notify_invoice_sent(invoice)
        
        return True
    
    @staticmethod
    @transaction.atomic
    def record_payment(
        invoice: Invoice,
        amount: Decimal,
        payment_method: str = PaymentMethod.CASH,
        reference_number: str = '',
        notes: str = '',
        recorded_by: Optional[User] = None,
    ) -> Payment:
        """
        Record a payment for an invoice.
        
        Args:
            invoice: Invoice being paid
            amount: Payment amount
            payment_method: Method of payment
            reference_number: External reference
            notes: Payment notes
            recorded_by: User recording the payment
        
        Returns:
            Created Payment instance
        """
        payment = Payment.objects.create(
            invoice=invoice,
            amount=amount,
            payment_method=payment_method,
            reference_number=reference_number,
            notes=notes,
            recorded_by=recorded_by,
        )
        
        InvoiceActivity.objects.create(
            invoice=invoice,
            activity_type='PAYMENT_RECEIVED',
            description=f'Payment of {amount} {invoice.currency} received',
            new_value={
                'amount': str(amount),
                'method': payment_method,
                'reference': reference_number,
            },
            performed_by=recorded_by,
        )
        
        # Notify patient of payment received
        InvoiceNotifier.notify_payment_received(invoice, payment)
        
        return payment
    
    @staticmethod
    def check_overdue_invoices() -> int:
        """
        Check and mark overdue invoices.
        
        Should be run daily via a scheduled task.
        
        Returns:
            Number of invoices marked as overdue
        """
        today = timezone.now().date()
        
        overdue = Invoice.objects.filter(
            status__in=[
                InvoiceStatus.SENT,
                InvoiceStatus.VIEWED,
                InvoiceStatus.PARTIALLY_PAID,
            ],
            due_date__lt=today,
        )
        
        count = 0
        for invoice in overdue:
            invoice.status = InvoiceStatus.OVERDUE
            invoice.save(update_fields=['status', 'updated_at'])
            
            InvoiceActivity.objects.create(
                invoice=invoice,
                activity_type='STATUS_CHANGED',
                description='Invoice marked as overdue',
                old_value={'status': invoice.status},
                new_value={'status': InvoiceStatus.OVERDUE},
            )
            
            # Notify about overdue
            InvoiceNotifier.notify_overdue(invoice)
            count += 1
        
        return count
    
    @staticmethod
    def get_provider_statistics(
        provider: Provider,
        start_date=None,
        end_date=None,
    ) -> Dict[str, Any]:
        """
        Get invoice statistics for a provider.
        
        Args:
            provider: Provider to get statistics for
            start_date: Optional start date filter
            end_date: Optional end date filter
        
        Returns:
            Dictionary of statistics
        """
        from django.db.models import Sum, Count
        
        queryset = Invoice.objects.filter(provider=provider)
        
        if start_date:
            queryset = queryset.filter(issue_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(issue_date__lte=end_date)
        
        totals = queryset.aggregate(
            total_amount=Sum('total'),
            total_paid=Sum('amount_paid'),
            invoice_count=Count('id'),
        )
        
        status_breakdown = {
            status: queryset.filter(status=status).count()
            for status, _ in InvoiceStatus.choices
        }
        
        return {
            'total_invoices': totals['invoice_count'] or 0,
            'total_amount': totals['total_amount'] or Decimal('0.00'),
            'total_paid': totals['total_paid'] or Decimal('0.00'),
            'total_outstanding': (
                (totals['total_amount'] or Decimal('0.00')) -
                (totals['total_paid'] or Decimal('0.00'))
            ),
            'status_breakdown': status_breakdown,
        }


class InvoiceNotifier:
    """
    Handles invoice-related notifications.
    
    Integrates with the notification system to send
    push notifications and WebSocket updates.
    """

    @staticmethod
    def _get_provider_name(invoice) -> str:
        """Get provider display name from invoice, never falling back to email."""
        name = invoice.provider.user.get_full_name()
        if name and name.strip():
            return name.strip()
        return 'Your healthcare provider'

    @staticmethod
    def _get_patient_name(invoice) -> str:
        """Get patient display name from invoice."""
        from common.utils import get_patient_display_name
        return get_patient_display_name(
            patient_user=invoice.patient_user,
            patient_record=invoice.patient_record,
        )
    
    @staticmethod
    def notify_invoice_sent(invoice: Invoice):
        """
        Notify patient that an invoice has been sent.
        
        Args:
            invoice: Invoice that was sent
        """
        try:
            from notifications.services import NotificationService
            
            patient_user = invoice.patient_user
            if not patient_user and invoice.patient_record:
                patient_user = invoice.patient_record.linked_user
            
            provider_name = InvoiceNotifier._get_provider_name(invoice)
            
            if patient_user:
                NotificationService.create_notification(
                    user=patient_user,
                    title='New Invoice',
                    body=f'{provider_name} sent you invoice #{invoice.invoice_number} for {invoice.total} {invoice.currency}.',
                    notification_type='INVOICE_CREATED',
                    data={
                        'invoice_id': str(invoice.id),
                        'invoice_number': invoice.invoice_number,
                        'total': str(invoice.total),
                        'currency': invoice.currency,
                        'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
                    },
                )
        except ImportError:
            pass
        except Exception:
            pass
    
    @staticmethod
    def notify_payment_received(invoice: Invoice, payment: Payment):
        """
        Notify patient and provider that a payment has been recorded.
        
        Args:
            invoice: Invoice that was paid
            payment: Payment that was recorded
        """
        try:
            from notifications.services import NotificationService
            
            patient_user = invoice.patient_user
            if not patient_user and invoice.patient_record:
                patient_user = invoice.patient_record.linked_user
            
            if invoice.status == InvoiceStatus.PAID:
                patient_title = 'Invoice Paid'
                patient_body = f'Your invoice #{invoice.invoice_number} has been paid in full.'
            else:
                patient_title = 'Payment Received'
                patient_body = f'Payment of {payment.amount} {invoice.currency} received for invoice #{invoice.invoice_number}. Remaining: {invoice.amount_due} {invoice.currency}'
            
            if patient_user:
                NotificationService.create_notification(
                    user=patient_user,
                    title=patient_title,
                    body=patient_body,
                    notification_type='PAYMENT_RECEIVED',
                    data={
                        'invoice_id': str(invoice.id),
                        'payment_id': str(payment.id),
                        'amount': str(payment.amount),
                        'status': invoice.status,
                    },
                )
        except ImportError:
            pass
        except Exception:
            pass
    
    @staticmethod
    def notify_overdue(invoice: Invoice):
        """
        Notify patient and provider that an invoice is overdue.
        """
        try:
            from notifications.services import NotificationService
            
            patient_user = invoice.patient_user
            if not patient_user and invoice.patient_record:
                patient_user = invoice.patient_record.linked_user
            
            provider_name = InvoiceNotifier._get_provider_name(invoice)
            
            if patient_user:
                NotificationService.create_notification(
                    user=patient_user,
                    title='Invoice Overdue',
                    body=f'Your invoice #{invoice.invoice_number} from {provider_name} for {invoice.amount_due} {invoice.currency} is now overdue.',
                    notification_type='INVOICE_OVERDUE',
                    data={
                        'invoice_id': str(invoice.id),
                        'invoice_number': invoice.invoice_number,
                        'amount_due': str(invoice.amount_due),
                        'due_date': invoice.due_date.isoformat(),
                    },
                )
        except ImportError:
            pass
        except Exception:
            pass
    
    @staticmethod
    def send_payment_reminder(invoice: Invoice):
        """
        Send a payment reminder for an unpaid invoice.
        
        Args:
            invoice: Invoice to remind about
        """
        try:
            from notifications.services import NotificationService
            
            patient_user = invoice.patient_user
            if not patient_user and invoice.patient_record:
                patient_user = invoice.patient_record.linked_user
            
            if not patient_user:
                return
            
            days_until_due = (invoice.due_date - timezone.now().date()).days if invoice.due_date else None
            
            if days_until_due and days_until_due > 0:
                body = f'Reminder: Invoice #{invoice.invoice_number} for {invoice.amount_due} {invoice.currency} is due in {days_until_due} days.'
            elif days_until_due == 0:
                body = f'Reminder: Invoice #{invoice.invoice_number} for {invoice.amount_due} {invoice.currency} is due today.'
            else:
                body = f'Reminder: Invoice #{invoice.invoice_number} for {invoice.amount_due} {invoice.currency} is overdue.'
            
            NotificationService.create_notification(
                user=patient_user,
                title='Payment Reminder',
                body=body,
                notification_type='PAYMENT_REMINDER',
                data={
                    'invoice_id': str(invoice.id),
                    'invoice_number': invoice.invoice_number,
                    'amount_due': str(invoice.amount_due),
                    'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
                },
            )
            
            # Log reminder
            InvoiceActivity.objects.create(
                invoice=invoice,
                activity_type='REMINDER_SENT',
                description='Payment reminder sent to patient',
            )
        except ImportError:
            pass
        except Exception:
            pass


class InvoicePDFData:
    """
    Prepares invoice data for PDF generation.
    
    The actual PDF generation is handled by the frontend,
    but this class prepares all necessary data.
    """
    
    @staticmethod
    def get_invoice_data(invoice: Invoice, language: str = 'en') -> Dict[str, Any]:
        """
        Get all data needed to generate an invoice PDF.
        
        Args:
            invoice: Invoice to prepare data for
            language: Language for localized content
        
        Returns:
            Dictionary with all invoice data
        """
        provider = invoice.provider
        provider_user = provider.user
        
        # Get provider details based on type
        provider_details = InvoicePDFData._get_provider_details(provider)
        
        # Get patient details
        patient_details = InvoicePDFData._get_patient_details(invoice, language)
        
        # Get items
        items = [
            {
                'order': item.order,
                'description': item.get_description(language),
                'quantity': str(item.quantity),
                'unit': item.unit,
                'unit_price': str(item.unit_price),
                'discount': str(item.discount_percentage),
                'total': str(item.total),
            }
            for item in invoice.items.all().order_by('order')
        ]
        
        # Get payments
        payments = [
            {
                'date': payment.payment_date.isoformat(),
                'amount': str(payment.amount),
                'method': payment.get_payment_method_display(),
                'reference': payment.reference_number,
            }
            for payment in invoice.payments.filter(is_refund=False)
        ]
        
        return {
            'invoice_number': invoice.invoice_number,
            'issue_date': invoice.issue_date.isoformat(),
            'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
            'status': invoice.status,
            'status_display': invoice.get_status_display(),
            
            'provider': provider_details,
            'patient': patient_details,
            
            'items': items,
            'currency': invoice.currency,
            
            'subtotal': str(invoice.subtotal),
            'tax_rate': str(invoice.tax_rate),
            'tax_amount': str(invoice.tax_amount),
            'discount_type': invoice.discount_type,
            'discount_value': str(invoice.discount_value),
            'discount_amount': str(invoice.discount_amount),
            'discount_reason': invoice.discount_reason,
            'total': str(invoice.total),
            
            'amount_paid': str(invoice.amount_paid),
            'amount_due': str(invoice.amount_due),
            
            'payments': payments,
            
            'notes': invoice.get_notes(language),
            'terms': invoice.terms,
        }
    
    @staticmethod
    def _get_provider_details(provider: Provider) -> Dict[str, Any]:
        """Get provider details for PDF."""
        user = provider.user
        details = {
            'name': user.get_full_name() or user.email,
            'email': user.email,
            'phone': getattr(user, 'phone', ''),
            'provider_type': provider.provider_type,
        }
        
        # Add type-specific details
        if provider.provider_type == ProviderType.DOCTOR and hasattr(provider, 'doctor_profile'):
            doctor = provider.doctor_profile
            details['license_number'] = getattr(doctor, 'license_number', '')
            details['specialty'] = getattr(doctor, 'specialty', '')
        
        elif provider.provider_type == 'CLINIC' and hasattr(provider, 'clinic_profile'):
            clinic = provider.clinic_profile
            details['name'] = getattr(clinic, 'name', details['name'])
            details['registration_number'] = getattr(clinic, 'registration_number', '')
        
        elif provider.provider_type == 'SELLER' and hasattr(provider, 'seller_profile'):
            seller = provider.seller_profile
            details['business_name'] = getattr(seller, 'business_name', '')
            details['tax_id'] = getattr(seller, 'tax_id', '')
        
        return details
    
    @staticmethod
    def _get_patient_details(invoice: Invoice, language: str) -> Dict[str, Any]:
        """Get patient details for PDF."""
        if invoice.patient_user:
            user = invoice.patient_user
            return {
                'name': user.get_full_name() or user.email,
                'email': user.email,
                'phone': getattr(user, 'phone', ''),
            }
        
        if invoice.patient_record:
            record = invoice.patient_record
            return {
                'name': f"{record.first_name} {record.last_name}".strip(),
                'patient_id': record.patient_unique_id,
                'phone': getattr(record, 'phone', ''),
            }
        
        return {'name': 'Unknown Patient'}
